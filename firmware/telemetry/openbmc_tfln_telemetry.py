#!/usr/bin/env python3
"""
OpenBMC TFLN Telemetry Daemon

Reads real-time health metrics from the TFLN Quantum Photonic Accelerator
via CXL memory-mapped I/O registers and pushes telemetry to the local
OpenBMC/FBPipe daemon for cluster-level monitoring (Meta Flogo/FBPipe).

CXL Register Map (Base: 0x4000_0000):
  0x2000  SILICON_TEMP      — Die temperature (0.01 K resolution)
  0x2004  PHOTOREFRACTIVE_DRIFT — V_pi drift in millivolts
  0x2008  INSERTION_LOSS    — Optical insertion loss (0.1 dBm resolution, -30 dBm offset)
  0x200C  TRIGGER_COUNT     — Total DAC trigger events (32-bit counter)
  0x2010  FAULT_COUNT       — Total optical fault events (16-bit)
  0x2014  CHANNEL_STATUS    — Per-channel SNSPD power-OK bitmask (8-bit)
  0x2018  MZI_MESH_FIDELITY — Matrix fidelity metric (16-bit, 0=worst, 65535=perfect)
  0x201C  LASER_DIODE_TEMP  — III-V laser diode junction temp (0.01 K resolution)

Fault Mitigation Actions:
  - Insertion loss < -3.0 dBm → Trigger RTL waveguide rerouting fallback
  - Photorefractive drift > 50 mV → Null voltage reset + V_pi recalibration
  - Laser diode temp > 350 K → Fallback clock slewing + backup laser switch
  - Channel status bitmask fault → FPGA MZI path reallocation

Integration:
  - Runs as a systemd service on the OpenBMC controller
  - Pushes JSON telemetry to http://localhost:8080/api/v1/telemetry/tfln_qpu
  - 1 Hz polling rate (configurable via TELEMETRY_INTERVAL_S)
"""

import json
import time
import struct
import logging
import argparse
from typing import Dict, Optional

logger = logging.getLogger("tfln_telemetry")

# CXL Bus Base Address for Telemetry Registers
CXL_BASE_ADDR = 0x40000000

# Register Offsets
REG_TEMP               = 0x2000
REG_DRIFT_OFFSET       = 0x2004
REG_INSERT_LOSS        = 0x2008
REG_TRIGGER_COUNT      = 0x200C
REG_FAULT_COUNT        = 0x2010
REG_CHANNEL_STATUS     = 0x2014
REG_MZI_FIDELITY       = 0x2018
REG_LASER_DIODE_TEMP   = 0x201C

# Fault Thresholds
THRESHOLD_INSERTION_LOSS_DBM = -3.0
THRESHOLD_DRIFT_MV = 50
THRESHOLD_LASER_TEMP_K = 350.0

# Telemetry endpoint
TELEMETRY_ENDPOINT = "http://localhost:8080/api/v1/telemetry/tfln_qpu"
TELEMETRY_INTERVAL_S = 1.0


class CXLMemoryInterface:
    """Abstraction for CXL memory-mapped register access.

    In production, this opens /dev/mem and maps the CXL BAR.
    In simulation mode, returns synthetic telemetry data.
    """

    def __init__(self, base_addr: int = CXL_BASE_ADDR, simulate: bool = True):
        self.base_addr = base_addr
        self.simulate = simulate
        self._mmap = None
        self._sim_tick = 0

    def open(self) -> None:
        if self.simulate:
            logger.info("Running in simulation mode (no /dev/mem access)")
            return

        import mmap
        import os
        page_size = os.sysconf("SC_PAGE_SIZE")
        fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
        self._mmap = mmap.mmap(fd, page_size, offset=self.base_addr)
        os.close(fd)
        logger.info(f"CXL memory mapped at 0x{self.base_addr:08X}")

    def close(self) -> None:
        if self._mmap:
            self._mmap.close()

    def read_u32(self, offset: int) -> int:
        if self.simulate:
            return self._simulate_register(offset)
        self._mmap.seek(offset)
        return struct.unpack("<I", self._mmap.read(4))[0]

    def _simulate_register(self, offset: int) -> int:
        """Generate synthetic telemetry for testing without hardware."""
        import random
        self._sim_tick += 1
        sim = {
            REG_TEMP: 30000 + random.randint(-50, 50),            # ~300 K
            REG_DRIFT_OFFSET: random.randint(5, 40),              # 5-40 mV drift
            REG_INSERT_LOSS: 280 + random.randint(-10, 10),       # ~-2.0 dBm
            REG_TRIGGER_COUNT: self._sim_tick * 250,              # 250 triggers/sec
            REG_FAULT_COUNT: random.randint(0, 2),                # rare faults
            REG_CHANNEL_STATUS: 0xFF,                             # all channels OK
            REG_MZI_FIDELITY: 64000 + random.randint(-500, 500), # ~97.6% fidelity
            REG_LASER_DIODE_TEMP: 31500 + random.randint(-100, 100),  # ~315 K
        }
        return sim.get(offset, 0)


class TFLNTelemetryDaemon:
    """Main telemetry collection and fault monitoring daemon."""

    def __init__(self, cxl: CXLMemoryInterface, push_url: str = TELEMETRY_ENDPOINT):
        self.cxl = cxl
        self.push_url = push_url
        self.running = False
        self.total_faults = 0
        self.reroute_events = 0

    def read_telemetry(self) -> Dict:
        """Read all telemetry registers and convert to human-readable metrics."""
        raw_temp = self.cxl.read_u32(REG_TEMP)
        raw_drift = self.cxl.read_u32(REG_DRIFT_OFFSET)
        raw_loss = self.cxl.read_u32(REG_INSERT_LOSS)
        raw_triggers = self.cxl.read_u32(REG_TRIGGER_COUNT)
        raw_faults = self.cxl.read_u32(REG_FAULT_COUNT)
        raw_channels = self.cxl.read_u32(REG_CHANNEL_STATUS)
        raw_fidelity = self.cxl.read_u32(REG_MZI_FIDELITY)
        raw_laser = self.cxl.read_u32(REG_LASER_DIODE_TEMP)

        return {
            "timestamp": int(time.time()),
            "silicon_temp_k": raw_temp * 0.01,
            "photorefractive_drift_mv": raw_drift,
            "insertion_loss_dbm": (raw_loss * 0.1) - 30.0,
            "trigger_count": raw_triggers,
            "fault_count": raw_faults,
            "channel_status_bitmask": f"0x{raw_channels:02X}",
            "channels_active": bin(raw_channels).count("1"),
            "mzi_mesh_fidelity_pct": (raw_fidelity / 65535.0) * 100.0,
            "laser_diode_temp_k": raw_laser * 0.01,
        }

    def check_faults(self, telemetry: Dict) -> list:
        """Check telemetry against fault thresholds and return actions."""
        actions = []

        # Optical power drop > 3 dB
        if telemetry["insertion_loss_dbm"] < THRESHOLD_INSERTION_LOSS_DBM:
            actions.append({
                "fault": "OPTICAL_POWER_DROP",
                "severity": "CRITICAL",
                "value": f"{telemetry['insertion_loss_dbm']:.1f} dBm",
                "action": "RTL_WAVEGUIDE_REROUTE",
                "description": "Triggering FPGA waveguide rerouting to standby MZI paths"
            })
            self.reroute_events += 1

        # Photorefractive drift exceeds threshold
        if telemetry["photorefractive_drift_mv"] > THRESHOLD_DRIFT_MV:
            actions.append({
                "fault": "PHOTOREFRACTIVE_DRIFT",
                "severity": "WARNING",
                "value": f"{telemetry['photorefractive_drift_mv']} mV",
                "action": "NULL_VOLTAGE_RESET",
                "description": "Applying reverse-bias clearing voltage and recalibrating V_pi"
            })

        # Laser diode thermal runaway
        if telemetry["laser_diode_temp_k"] > THRESHOLD_LASER_TEMP_K:
            actions.append({
                "fault": "LASER_THERMAL_RUNAWAY",
                "severity": "CRITICAL",
                "value": f"{telemetry['laser_diode_temp_k']:.1f} K",
                "action": "FALLBACK_CLOCK_SLEW",
                "description": "Throttling ASIC drive clock, switching to backup chassis laser"
            })

        # Channel dropout
        if telemetry["channels_active"] < 8:
            actions.append({
                "fault": "CHANNEL_DROPOUT",
                "severity": "WARNING",
                "value": f"{telemetry['channels_active']}/8 channels active",
                "action": "MZI_PATH_REALLOCATION",
                "description": "FPGA reallocating MZI paths around faulted channels"
            })

        self.total_faults += len(actions)
        return actions

    def push_telemetry(self, payload: Dict) -> bool:
        """Push telemetry JSON to OpenBMC/FBPipe daemon."""
        try:
            import urllib.request
            req = urllib.request.Request(
                self.push_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=1)
            return True
        except Exception:
            return False

    def run(self, interval_s: float = TELEMETRY_INTERVAL_S,
            max_iterations: Optional[int] = None) -> None:
        """Main telemetry polling loop."""
        self.running = True
        iteration = 0
        logger.info("TFLN Telemetry Daemon started")
        logger.info(f"Polling interval: {interval_s}s | Endpoint: {self.push_url}")

        try:
            while self.running:
                telemetry = self.read_telemetry()
                faults = self.check_faults(telemetry)

                payload = {
                    **telemetry,
                    "faults": faults,
                    "total_faults_session": self.total_faults,
                    "reroute_events_session": self.reroute_events,
                }

                pushed = self.push_telemetry(payload)

                if faults:
                    for f in faults:
                        logger.warning(
                            f"FAULT: {f['fault']} — {f['value']} → {f['action']}"
                        )

                logger.debug(
                    f"Tick {iteration}: temp={telemetry['silicon_temp_k']:.1f}K, "
                    f"loss={telemetry['insertion_loss_dbm']:.1f}dBm, "
                    f"fidelity={telemetry['mzi_mesh_fidelity_pct']:.1f}%, "
                    f"pushed={'OK' if pushed else 'FAIL'}"
                )

                iteration += 1
                if max_iterations and iteration >= max_iterations:
                    break
                time.sleep(interval_s)

        except KeyboardInterrupt:
            logger.info("Shutting down telemetry daemon.")
        finally:
            self.running = False


def main():
    parser = argparse.ArgumentParser(
        description="TFLN Quantum Photonic Accelerator — OpenBMC Telemetry Daemon"
    )
    parser.add_argument("--simulate", action="store_true", default=True,
                        help="Run in simulation mode without /dev/mem")
    parser.add_argument("--interval", type=float, default=1.0,
                        help="Polling interval in seconds")
    parser.add_argument("--iterations", type=int, default=None,
                        help="Max iterations (None = infinite)")
    parser.add_argument("--endpoint", type=str, default=TELEMETRY_ENDPOINT,
                        help="Telemetry push endpoint URL")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    cxl = CXLMemoryInterface(simulate=args.simulate)
    cxl.open()

    daemon = TFLNTelemetryDaemon(cxl, push_url=args.endpoint)

    try:
        daemon.run(interval_s=args.interval, max_iterations=args.iterations)
    finally:
        cxl.close()


if __name__ == "__main__":
    main()
