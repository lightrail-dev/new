run.sh
iverilog -o lightrail lightrail.v tb.v
vvp lightrail -vcd
gtkwave lightrail.vcd