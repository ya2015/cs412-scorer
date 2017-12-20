import agreement_utils
import sys
TEST= 3
count = TEST
def raw_input_test():
    while(count):
        sen = input("Test Sentences:\n")
        ans = agreement_utils.parse(sen, use_cache = False)
        count = count -1
def file_input_test():
    f = open("test/1.txt")
    for line in f.read().split("\n"):
        print("***************")
        print(line)
        print("***************")
        ans = agreement_utils.parse(line, use_cache = False)
        if ans[1]== 0:
            print("-----------AC-----------")
        else:
            print("-----------FAIL-----------")
        print("\n")
file_input_test()