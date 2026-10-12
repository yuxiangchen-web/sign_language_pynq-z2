set script_dir [file dirname [file normalize [info script]]]

cd $script_dir

set project_name image_preprocess_hls
set solution_name solution1
set top_name image_preprocess

open_project $project_name

open_solution $solution_name

add_files image_preprocess.h
add_files image_preprocess.cpp
add_files -tb tb_image_preprocess.cpp

set_top $top_name

set_part xc7z020clg400-1

create_clock -period 10 -name default

csim_design -clean
csynth_design

export_design \
    -format ip_catalog \
    -output D:/PYNQ/projects/sign-language-pynq/fpga/ip/image_preprocess_ip

exit