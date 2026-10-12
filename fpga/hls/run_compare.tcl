set here [file dirname [file normalize [info script]]]
cd $here
open_project compare_hls
set_top image_preprocess
add_files image_preprocess.cpp
add_files image_preprocess.h
add_files -tb tb_compare.cpp
foreach name {input_rgb.txt expected_0.txt expected_1.txt} {
    add_files -tb test_vectors/$name
}
open_solution solution1 -flow_target vivado
set_part xc7z020clg400-1
create_clock -period 10
csim_design -clean
exit
