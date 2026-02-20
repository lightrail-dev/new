"""
Refined CircuitMaker / Altium Project File Generator (20-Layer Stack)
"""

import os

def generate_circuitmaker_prj_20l(output_path):
    prj_content = [
        "[Design]",
        "Version=1.0",
        "ProjectType=PCB",
        "ManagedProjectGUID=",
        "ProjectName=LightRail_AI_20L_Stack",
        "",
        "[Document1]",
        "DocumentPath=lightrail_20l.kicad_pcb",
        "",
        "[Parameters]",
        "Parameter1=ProjectTitle|LightRail AI 20-Layer Intelligence Stack",
        "Parameter2=ProjectRevision|4.0",
        "Parameter3=ProjectDescription|Exascale Photonic AI Accelerator (20-Layer)",
        "",
        "[ProjectExtension]",
        "Extension=PCB",
        "",
        "[EngineEnvironment]",
        "Environment=CircuitMaker",
        ""
    ]
    
    with open(output_path, 'wb') as f:
        content_str = "\r\n".join(prj_content)
        f.write(content_str.encode('windows-1252'))
    
    print(f"Generated 20-Layer CircuitMaker Project: {output_path}")

if __name__ == "__main__":
    prj_file = r"C:\Users\bolao\Downloads\LightRail_AI_20L_Stack.PrjPcb"
    generate_circuitmaker_prj_20l(prj_file)
