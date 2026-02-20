"""
Refined CircuitMaker / Altium Project File Generator
Uses standard Altium/CircuitMaker 2.x structure.
"""

import os

def generate_circuitmaker_prj(output_path):
    # CircuitMaker/Altium often prefers Windows-1252 or CRLF line endings.
    # We will use standard Altium Project Sections.
    prj_content = [
        "[Design]",
        "Version=1.0",
        "ProjectType=PCB",
        "ManagedProjectGUID=",
        "ProjectName=LightRail_AI_CPO",
        "",
        "[Document1]",
        "DocumentPath=LightRail_AI_CPO.SchDoc",
        "",
        "[Document2]",
        "DocumentPath=lightrail_cpo.kicad_pcb",
        "",
        "[Configuration1]",
        "Name=Default Configuration",
        "ParameterCount=0",
        "ConstraintFileCount=0",
        "ReleaseEnvironmentCount=0",
        "ReleaseTargetCount=0",
        "",
        "[ModificationLog]",
        "ModificationCount=0",
        "",
        "[Parameters]",
        "Parameter1=ProjectTitle|LightRail AI CPO",
        "",
        "[ProjectExtension]",
        "Extension=PCB",
        "",
        "[EngineEnvironment]",
        "Environment=CircuitMaker",
        ""
    ]
    
    # Write with CRLF and ANSI (Windows-1252) encoding which is most compatible with Altium
    with open(output_path, 'wb') as f:
        content_str = "\r\n".join(prj_content)
        f.write(content_str.encode('windows-1252'))
    
    print(f"Generated Optimized CircuitMaker Project: {output_path}")

if __name__ == "__main__":
    # Target path in downloads
    prj_file = r"C:\Users\bolao\Downloads\LightRail_AI_CPO.PrjPcb"
    generate_circuitmaker_prj(prj_file)
