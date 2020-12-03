#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
IF: Input Feeder (former Decompressor)
BDS: bayer downscaling
GDC: Geometric Distortion Correction block
DVS: Digital video stabilization
SF: scale factor
'''
import sys
import math

LOG_DBG = 0

FILTER_W = 4
FILTER_H = 4

IF_ALIGN_W = 2
IF_ALIGN_H = 4
BDS_ALIGN_W = 2
BDS_ALIGN_H = 4

IF_CROP_MAX_W = 40
IF_CROP_MAX_H = 540

BDS_SF_MAX = 2.5
BDS_SF_MIN = 1
BDS_SF_STEP = 1/32

YUV_SF_MAX = 16
YUV_SF_MIN = 1
YUV_SF_STEP = 1/4

PIPE_CONFIGS = []


def gen_list_by_step(start, end, step):
    '''generate list by step'''
    result = []
    for i in range(int(start / step), int(end / step) + 1):
        result.append(i * step)
    return result


BDS_SF_LIST = gen_list_by_step(BDS_SF_MIN, BDS_SF_MAX, BDS_SF_STEP)
YUV_SF_LIST = gen_list_by_step(YUV_SF_MIN, YUV_SF_MAX, YUV_SF_STEP)


def pixel_align_decrease(pixels, align):
    '''pixel align decrease.'''
    return math.floor(pixels / align) * align


def pixel_align_increase(pixels, align):
    '''pixel align increase.'''
    if pixels % align != 0:
        return(math.floor(pixels / align) + 1) * align

    return pixels


def find_nearest_value(input_value, available_values, up_down=0):
    '''find nearest value in available_values.'''
    if input_value < available_values[0]:
        return available_values[0]
    if input_value > available_values[-1]:
        return available_values[-1]

    nearest_idx = 0
    min_diff = abs(available_values[0] - input_value)
    for i in range(1, len(available_values)):
        diff = abs(input_value - available_values[i])
        if diff < min_diff:
            min_diff = diff
            nearest_idx = i

    if up_down < 0 and input_value < available_values[nearest_idx]:
        nearest_value = available_values[nearest_idx - 1]
    elif up_down > 0 and input_value > available_values[nearest_idx]:
        nearest_value = available_values[nearest_idx + 1]
    else:
        nearest_value = available_values[nearest_idx]

    return nearest_value


def set_valid_value(input_value, min_value, max_value):
    '''set valid value'''
    value = input_value
    if input_value < min_value:
        value = min_value

    if input_value > max_value:
        value = max_value
    return value


def find_height(if_out, bds_out, gdc_out, crop_height, bds_sf):
    '''base on if_w and bds_sf, find if_h and bds_h are both integer'''
    min_if_h = if_out[1] - IF_CROP_MAX_H
    min_bds_h = gdc_out[1] + FILTER_H * 2
    if_w = if_out[0]
    bds_w = bds_out[0]

    if LOG_DBG > 3:
        print("bds_sf:%f, bds_w:%f" % (bds_sf, bds_w))

    if crop_height == 0:
        if_h = pixel_align_increase(if_out[1], IF_ALIGN_H)
        while if_h >= min_if_h and if_h / bds_sf >= min_bds_h:
            bds_h = if_h / bds_sf
            if if_h % IF_ALIGN_H == 0 and bds_h % BDS_ALIGN_H == 0:
                pipe_conf = \
                  [1, bds_sf, if_w, if_h, bds_w, bds_h, gdc_out[0], gdc_out[1]]
                PIPE_CONFIGS.append(pipe_conf)
                break

            if_h -= IF_ALIGN_H
    else:
        finded_sf = [0, 0]
        finded_if_h = [0, 0]
        estimate_if_h = if_w * gdc_out[1] / gdc_out[0]
        estimate_if_h = set_valid_value(estimate_if_h, min_if_h, if_out[1])

        if_h = pixel_align_increase(estimate_if_h, IF_ALIGN_H)
        if LOG_DBG > 3:
            print("estimate_if_h:%f, if_h:%f" % (estimate_if_h, if_h))
        while if_h >= min_if_h and if_h <= if_out[1] and if_h / bds_sf >= min_bds_h:
            bds_h = if_h / bds_sf
            if bds_h % BDS_ALIGN_H == 0:
                finded_sf[0] = 1
                finded_if_h[0] = if_h
                break
            if_h -= IF_ALIGN_H

        if_h = pixel_align_increase(estimate_if_h, IF_ALIGN_H)
        while if_h >= min_if_h and if_h <= if_out[1] and if_h / bds_sf >= min_bds_h:
            bds_h = if_h / bds_sf
            if bds_h % BDS_ALIGN_H == 0:
                finded_sf[1] = 1
                finded_if_h[1] = if_h
                break
            if_h += IF_ALIGN_H

        if finded_sf[0] == 1:
            if_h = finded_if_h[0]

        if finded_sf[1] == 1:
            if_h = finded_if_h[1]

        if finded_sf[0] == 1 or finded_sf[1] == 1:
            pipe_conf = \
              [1, bds_sf, if_w, if_h, bds_w, bds_h, gdc_out[0], gdc_out[1]]
            if LOG_DBG > 1:
                print("IF: %dx%d BDS:%dx%d GDC:%dx%d" % (if_w, if_h, bds_w, bds_h, \
                                                         gdc_out[0], gdc_out[1]))
            PIPE_CONFIGS.append(pipe_conf)


def find_bds_sf(if_out, gdc_out, crop_height, sf_step, bds_sf):
    '''base on if_w, find a bds_sf, ensure  bds_w is integer'''
    if_w = if_out[0]
    if_h = if_out[1]
    min_bds_w = gdc_out[0] + FILTER_W * 2
    min_bds_h = gdc_out[1] + FILTER_H * 2
    while BDS_SF_MAX >= bds_sf >= BDS_SF_MIN:
        bds_w = if_w / bds_sf
        bds_h = if_h / bds_sf

        if bds_w % BDS_ALIGN_W == 0 and bds_w >= min_bds_w and \
           bds_h % BDS_ALIGN_H == 0 and bds_h >= min_bds_h:
            bds_out = [bds_w, 0]
            find_height(if_out, bds_out, gdc_out, crop_height, bds_sf)
        bds_sf += sf_step


def find_available_config(ipu_in, gdc_out, crop_height, sf_step):
    '''find a bds sf, ensure  both if_out and bds_out are integer'''
    esti_bds_sf = ipu_in[0] / gdc_out[0]
    base_bds_sf = find_nearest_value(esti_bds_sf, BDS_SF_LIST, -1)

    if_w = pixel_align_increase(ipu_in[0], IF_ALIGN_W)
    if_h = pixel_align_increase(ipu_in[1], IF_ALIGN_H)
    min_if_w = ipu_in[0] - IF_CROP_MAX_W
    min_if_h = ipu_in[1] - IF_CROP_MAX_H
    while if_w >= min_if_w :
        while if_h >= min_if_h :
            if_output = [if_w, if_h]
            find_bds_sf(if_output, gdc_out, crop_height, sf_step, base_bds_sf)
            if_h -= IF_ALIGN_H
        if_w -= IF_ALIGN_W

    if_w = pixel_align_increase(ipu_in[0], IF_ALIGN_W)
    if_h = pixel_align_increase(ipu_in[1], IF_ALIGN_H)
    min_if_w = ipu_in[0] - IF_CROP_MAX_W
    min_if_h = ipu_in[1] - IF_CROP_MAX_H

    while if_h >= min_if_h :
        while if_w >= min_if_w :
            if_output = [if_w, if_h]
            find_bds_sf(if_output, gdc_out, crop_height, sf_step, base_bds_sf)
            if_w -= IF_ALIGN_W
        if_h -= IF_ALIGN_H

def calc_fov(input_res, pipe_conf):
    '''calc fov'''
    if_crop_w = input_res[0] - pipe_conf[2]
    if_crop_h = input_res[1] - pipe_conf[3]

    gdc_crop_w = (pipe_conf[4] - pipe_conf[6] * pipe_conf[0]) * pipe_conf[1]
    gdc_crop_h = (pipe_conf[5] - pipe_conf[7] * pipe_conf[0]) * pipe_conf[1]
    fov_w = (input_res[0] - (if_crop_w + gdc_crop_w)) / input_res[0]
    fov_h = (input_res[1] - (if_crop_h + gdc_crop_h)) / input_res[1]
    if LOG_DBG > 4:
        print("[calc_fov] fov_w:%f, fov_h:%f" % (fov_w, fov_h))
    return fov_w, fov_h


def find_maxfov_config(input_res):
    '''find_max fov_config'''
    if PIPE_CONFIGS is None or len(PIPE_CONFIGS) == 0:
        print("fatal")
    fov_max_w = 0
    fov_max_h = 0
    max_fov_config = PIPE_CONFIGS[0]
    for pipe_config in PIPE_CONFIGS:
        fov_w, fov_h = calc_fov(input_res, pipe_config)
        if fov_w > fov_max_w:
            fov_max_w = fov_w
            fov_max_h = fov_h
            max_fov_config = pipe_config
        elif fov_w == fov_max_w:
            if fov_h > fov_max_h:
                fov_max_h = fov_h
                max_fov_config = pipe_config

    print("-------- The selected pipe configuration: --------------")
    print("output_res_if:%dx%d" % (max_fov_config[2], max_fov_config[3]))
    print("output_res_bds:%dx%d" % (max_fov_config[4], max_fov_config[5]))
    print("output_res_gdc:%dx%d" % (max_fov_config[6], max_fov_config[7]))
    print("FOV Horizontal:%f, FOV vertical:%f" % (fov_max_w, fov_max_h))

    return max_fov_config[2:]


def save_available_config(ipu_in, gdc_out, if_crop_h):
    '''save available config'''
    find_available_config(ipu_in, gdc_out, if_crop_h, -BDS_SF_STEP)
    find_available_config(ipu_in, gdc_out, if_crop_h, BDS_SF_STEP)


def print_param_error_info(error_type):
    '''print param error info'''
    if error_type == 'len':
        print("number error, please use command like follow:")
    elif error_type == 'size':
        print("input > main > vf, please use command like follow:")
    elif error_type == 'align':
        print("out/vf width shoule be multiple of 64, height should be multiple of 4")
    else:
        print("%s error, please use command like follow:" % (error_type))

    print("    1 output:")
    print("        python3 pipe_config.py input=3280x2464 main=320x240")
    print("    2 outputs:")
    print("        python3 pipe_config.py input=3280x2464 main=1280x960 vf=320x240")
    sys.exit()


def param_check(key, params):
    '''param check'''
    if '=' in params:
        input_param = params.split('=')
        if len(input_param) != 2 or input_param[0] != key:
            print_param_error_info(key)
        else:
            if 'x' in input_param[1]:
                in_res = input_param[1].split('x')
                num = len(in_res)
                if num == 2 and in_res[0].isdigit() and in_res[1].isdigit():
                    return [int(in_res[0]), int(in_res[1])]

                print_param_error_info(key)
            else:
                print_param_error_info(key)
    else:
        print_param_error_info(key)

    return None


def param_parse(params):
    '''param parse'''
    if len(params) > 3 or len(params) < 2:
        print_param_error_info('len')
    in_res = param_check('input', params[0])
    out_main = param_check('main', params[1])

    if len(params) == 2:
        out_vf = None
        if in_res[0] < out_main[0] or in_res[1] < out_main[1]:
            print_param_error_info('size')
        if out_main[0] % 64 != 0 or out_main[1] % 4 != 0:
            print_param_error_info('align')
    else:
        out_vf = param_check('vf', params[2])
        if in_res[0] < out_main[0] or in_res[1] < out_main[1]:
            print_param_error_info('size')
        if out_main[0] < out_vf[0] or out_main[1] < out_vf[1]:
            print_param_error_info('size')
        if out_main[0] % 64 != 0 or out_main[1] % 4 != 0 or \
           out_vf[0] % 64 != 0 or out_vf[1] % 4 != 0:
            print_param_error_info('align')

    return in_res, out_main, out_vf


def is_diff_ratio(res_in, res_out):
    '''check if diff ratio'''
    if abs(res_in[0]/res_in[1] - res_out[0]/res_out[1]) > 0.1:
        return 1

    return 0


def calc_gdc_out(ipu_in, out_main, out_vf):
    '''calc gdc out'''
    if out_vf is not None:
        gdc_w = out_main[0]
        gdc_h = max(out_main[1], out_main[0] * out_vf[1] / out_vf[0])
        gdc_out = [gdc_w, gdc_h]
    else:
        if is_diff_ratio(ipu_in, out_main):
            gdc_out = out_main
        else:
            bds_sf = 1
            estimate_total_sf = ipu_in[0] / out_main[0]
            if estimate_total_sf > 2:
                bds_sf = 2
            esti_yuv_sf = estimate_total_sf / bds_sf
            yuv_sf = find_nearest_value(esti_yuv_sf, YUV_SF_LIST, up_down=0)
            gdc_out = [out_main[0] * yuv_sf, out_main[1] * yuv_sf]

    if LOG_DBG > 0:
        print("[calc_gdc_out]gdc_out: %d x %d" % (gdc_out[0], gdc_out[1]))

    return gdc_out


def pipe_conf_api(ipu_in, ipu_out_main, ipu_out_vf):
    '''for group generate'''
    PIPE_CONFIGS.clear()
    gdc_out = calc_gdc_out(ipu_in, ipu_out_main, ipu_out_vf)

    if_crop_height = is_diff_ratio(ipu_in, gdc_out)

    save_available_config(ipu_in, gdc_out, if_crop_height)
    results = find_maxfov_config(ipu_in)
    results = list(map(int, results))

    return list(map(str, results))


def pipe_config_gen(params):
    '''pipe config generate'''
    [ipu_input, ipu_out_main, ipu_out_vf] = param_parse(params)
    gdc_output = calc_gdc_out(ipu_input, ipu_out_main, ipu_out_vf)

    if_crop_height = is_diff_ratio(ipu_input, gdc_output)

    save_available_config(ipu_input, gdc_output, if_crop_height)

    find_maxfov_config(ipu_input)


if __name__ == "__main__":
    PIPE_CONFIGS.clear()
    pipe_config_gen(sys.argv[1:])
