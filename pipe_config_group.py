#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
this py can generate group graph configs
'''
import sys
import csv
import imp
import pipe_config
imp.reload(pipe_config)


def param_parse(params):
    '''param parse.'''
    if 'x' in params:
        res = params.split('x')
        if len(res) == 2 and res[0].isdigit() and res[1].isdigit():
            return [int(res[0]), int(res[1])]

        return None

    return None


def param_check(in_res, out_main, out_vf, line_num):
    '''param check.'''
    ret = True
    if in_res is None or out_main is None:
        print("line: %d, input and out_main error" % (line_num))
        ret = False
    elif out_vf is None:
        if in_res[0] < out_main[0] or in_res[1] < out_main[1]:
            print("line: %d, size should be input > vf" % (line_num))
            ret = False
        if out_main[0] % 64 != 0 or out_main[1] % 4 != 0:
            print("out width shoule be multiple of 64, height should be multiple of 4")
            ret = false
    else:
        if in_res[0] < out_main[0] or in_res[1] < out_main[1]:
            print("line: %d, size should be input > main > vf" % (line_num))
            ret = False
        elif out_main[0] < out_vf[0] or out_main[1] < out_vf[1]:
            print("line: %d, size should be input > main > vf" % (line_num))
            ret = False
        if out_main[0] % 64 != 0 or out_main[1] % 4 != 0 or \
           out_vf[0] % 64 != 0 or out_vf[1] % 4 != 0:
            print("out/vf width shoule be multiple of 64, height should be multiple of 4")
            ret = false

    return ret


def need_check_reslut(expect_values):
    '''if need check reslut.'''
    for i in expect_values:
        if i == '':
            return False

    return True


def check_reslut(expect_values, actual_values):
    '''check reslut.'''
    results = ['same']
    for i in range(0, 6):
        if expect_values[i] != actual_values[i]:
            results = ['diff']
            break

    return results


def pipe_config_gen(input_csv):
    '''pipe config generate'''
    input_file = open(input_csv, 'r')
    lines = input_file.readlines()
    input_file.close()

    output_name = 'result_' + input_csv
    with open(output_name, 'w', newline='')as output_file:
        writer = csv.writer(output_file)
        row = []

        curr_line = 0
        for line in lines[:2]:
            curr_line += 1
            row = line.split(',')
            writer.writerow(row)

        for line in lines[2:]:
            curr_line += 1
            result = ['same']
            row = line.split(',')
            input_res = param_parse(row[0])
            out_main = param_parse(row[1])
            if row[2] == '':
                out_vf = None
            else:
                out_vf = param_parse(row[2])
            if not param_check(input_res, out_main, out_vf, curr_line):
                row[15] = 'param error'
                print(row)
                writer.writerow(row)
                continue
            actual_val = pipe_config.pipe_conf_api(input_res, out_main, out_vf)
            row = row[:9]
            row += actual_val

            if need_check_reslut(row[3:9]):
                result = check_reslut(row[3:9], row[9:15])
                row += result
            print(row)
            writer.writerow(row)
    output_file.close()


if __name__ == "__main__":
    pipe_config_gen(sys.argv[1])
