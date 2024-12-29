# full = 10
# partial = 20

# divide = partial // 3
# remainder = full % 3
# used = divide * 3

# final_partial = partial - used
# final_full = full + divide

# print(final_partial)
# print(final_full)


# secondary_defects_name = [{"partial black": 3}, {"partial sour": 3}]

# # Check if "partial black" exists as a key in any of the dictionaries
# if any("partial black" in defect for defect in secondary_defects_name):
#     print("Yes")
# else:
#     print("No")

a = {"partial black": 3}
a["partial black"] = a["partial black"], 1

print(a["partial black"][1])
