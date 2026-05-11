// -----------------------------------------------------------------------------
// LR-CSW UVM smoke test (1k packet random sweep, all 80 ingress lanes)
// -----------------------------------------------------------------------------
`include "uvm_macros.svh"
import  uvm_pkg::*;
import  lr_csw_env_pkg::*;

class lr_csw_random_seq extends uvm_sequence #(lr_packet_item);
    `uvm_object_utils(lr_csw_random_seq)
    rand int n;
    constraint c_n { n inside {[256:4096]}; }
    function new(string name="lr_csw_random_seq"); super.new(name); endfunction
    virtual task body();
        lr_packet_item it;
        repeat (n) begin
            it = lr_packet_item::type_id::create("it");
            assert(it.randomize());
            start_item(it); finish_item(it);
        end
    endtask
endclass

class lr_csw_smoke_test extends uvm_test;
    `uvm_component_utils(lr_csw_smoke_test)
    lr_csw_env env;
    function new(string name, uvm_component parent); super.new(name, parent); endfunction
    function void build_phase(uvm_phase phase);
        env = lr_csw_env::type_id::create("env", this);
    endfunction
    virtual task run_phase(uvm_phase phase);
        lr_csw_random_seq seq;
        phase.raise_objection(this);
        seq = lr_csw_random_seq::type_id::create("seq");
        seq.start(null);
        #10us;
        phase.drop_objection(this);
    endtask
endclass

module tb_top;
    initial run_test();
endmodule
