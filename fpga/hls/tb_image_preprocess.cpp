#include "image_preprocess.h"

#include <cassert>
#include <iostream>

int main() {
    hls::stream<axis_rgb_t> input_stream;
    hls::stream<axis_mask_t> output_stream;

    // 使用红色像素作为前景测试样本。
    // 红色大致对应：
    // Y  ≈ 76
    // Cr ≈ 255
    // Cb ≈ 85
    const ap_uint<8> y_min = 45;
    const ap_uint<8> y_max = 225;

    const ap_uint<8> cr_min = 135;
    const ap_uint<8> cr_max = 190;

    const ap_uint<8> cb_min = 80;
    const ap_uint<8> cb_max = 145;
    const ap_uint<1> enable_morphology = 0;

    // 生成一帧测试图像。
    for (int row = 0; row < IMAGE_HEIGHT; row++) {
        for (int col = 0; col < IMAGE_WIDTH; col++) {
            axis_rgb_t pixel;

            bool is_test_foreground =
                (row == 0 && col == 0);

            if (is_test_foreground) {
                // 第一个像素：红色，应该被识别为前景
                pixel.data = (200 << 16) | (140 << 8) | 110;
            } else {
                // 其他像素：黑色，应该被识别为背景
                pixel.data = 0;
            }

            pixel.keep = 1;
            pixel.strb = 1;
            pixel.user = (row == 0 && col == 0) ? 1 : 0;
            pixel.last =
                (row == IMAGE_HEIGHT - 1 &&
                 col == IMAGE_WIDTH - 1) ? 1 : 0;
            pixel.id = 0;
            pixel.dest = 0;

            input_stream.write(pixel);
        }
    }

    // 调用待测试的 HLS 顶层函数。
    image_preprocess(
        input_stream,
        output_stream,
        y_min,
        y_max,
        cr_min,
        cr_max,
        cb_min,
        cb_max,
        enable_morphology
    );

    // 检查输出像素数量。
    int output_count = 0;

    while (!output_stream.empty()) {
        axis_mask_t output_pixel = output_stream.read();

        if (output_count == 0) {
            // 第一个像素是红色，应该为前景 255。
            assert(output_pixel.data == 255);
            assert(output_pixel.user == 1);
            assert(output_pixel.last == 0);
        }

        if (output_count == IMAGE_PIXELS - 1) {
            // 最后一个像素是黑色，应该为背景 0。
            assert(output_pixel.data == 0);
            assert(output_pixel.user == 0);
            assert(output_pixel.last == 1);
        }

        output_count++;
    }

    assert(output_count == IMAGE_PIXELS);

    std::cout << "C simulation passed." << std::endl;
    std::cout << "Output pixels: "
              << output_count << std::endl;

    return 0;
}