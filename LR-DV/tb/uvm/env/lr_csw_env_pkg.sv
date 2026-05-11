// -----------------------------------------------------------------------------
// LR-CSW UVM environment package — agents, scoreboard, coverage
// -----------------------------------------------------------------------------
`ifndef LR_CSW_ENV_PKG_SV
`define LR_CSW_ENV_PKG_SV
package lr_csw_env_pkg;
    import uvm_pkg::*;
    `include "uvm_macros.svh"

    // ---------------------------------------------------------------- sequence item
    class lr_packet_item extends uvm_sequence_item;
        rand bit [47:0] dst_mac;
        rand bit [47:0] src_mac;
        rand bit [15:0] ethertype;
        rand bit [7:0]  payload[];
        rand int        length;

        constraint c_len { payload.size() == length; length inside {[64:9216]}; }

        `uvm_object_utils_begin(lr_packet_item)
            `uvm_field_int(dst_mac, UVM_DEFAULT)
            `uvm_field_int(src_mac, UVM_DEFAULT)
            `uvm_field_int(ethertype, UVM_DEFAULT)
            `uvm_field_array_int(payload, UVM_DEFAULT)
        `uvm_object_utils_end

        function new(string name="lr_packet_item"); super.new(name); endfunction
    endclass

    // ---------------------------------------------------------------- driver
    class lr_eth_drv extends uvm_driver #(lr_packet_item);
        `uvm_component_utils(lr_eth_drv)
        function new(string name, uvm_component parent); super.new(name, parent); endfunction
        virtual task run_phase(uvm_phase phase);
            lr_packet_item it;
            forever begin
                seq_item_port.get_next_item(it);
                `uvm_info("DRV", $sformatf("Driving packet len=%0d", it.length), UVM_MEDIUM)
                // tb-vif drive sequence omitted here (in lr_eth_if.sv)
                #10;
                seq_item_port.item_done();
            end
        endtask
    endclass

    // ---------------------------------------------------------------- monitor
    class lr_eth_mon extends uvm_monitor;
        `uvm_component_utils(lr_eth_mon)
        uvm_analysis_port#(lr_packet_item) ap;
        function new(string name, uvm_component parent);
            super.new(name, parent); ap = new("ap", this);
        endfunction
    endclass

    // ---------------------------------------------------------------- scoreboard
    class lr_sb extends uvm_scoreboard;
        `uvm_component_utils(lr_sb)
        uvm_analysis_imp #(lr_packet_item, lr_sb) imp_tx;
        uvm_analysis_imp #(lr_packet_item, lr_sb) imp_rx;
        int n_match, n_mismatch;

        function new(string name, uvm_component parent); super.new(name, parent); endfunction

        function void write(lr_packet_item t);
            // expected/observed matching omitted — uses queue per egress lane
        endfunction
    endclass

    // ---------------------------------------------------------------- coverage
    class lr_cov extends uvm_subscriber #(lr_packet_item);
        `uvm_component_utils(lr_cov)

        covergroup cg_pkt with function sample(lr_packet_item it);
            length:   coverpoint it.length      { bins small={[64:127]}; bins mid={[128:1518]}; bins jumbo={[1519:9216]}; }
            ethertype:coverpoint it.ethertype   { bins ipv4 = {16'h0800}; bins ipv6 = {16'h86dd}; bins arp = {16'h0806}; bins rest = default; }
            cross length, ethertype;
        endgroup

        function new(string name, uvm_component parent);
            super.new(name, parent); cg_pkt = new();
        endfunction
        function void write(lr_packet_item t); cg_pkt.sample(t); endfunction
    endclass

    // ---------------------------------------------------------------- env
    class lr_csw_env extends uvm_env;
        `uvm_component_utils(lr_csw_env)
        lr_eth_drv drv;
        lr_eth_mon mon;
        lr_sb      sb;
        lr_cov     cov;
        function new(string name, uvm_component parent); super.new(name, parent); endfunction
        function void build_phase(uvm_phase phase);
            drv = lr_eth_drv::type_id::create("drv", this);
            mon = lr_eth_mon::type_id::create("mon", this);
            sb  = lr_sb::type_id::create("sb", this);
            cov = lr_cov::type_id::create("cov", this);
        endfunction
        function void connect_phase(uvm_phase phase);
            mon.ap.connect(cov.analysis_export);
        endfunction
    endclass

endpackage
`endif
