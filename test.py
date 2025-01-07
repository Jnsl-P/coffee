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


from datetime import datetime
import pytz

local_timezone = pytz.timezone('Asia/Manila')  # Replace with your local timezone, e.g., 'America/New_York'

def get_local_time():
    return datetime.now(local_timezone)
print(get_local_time().strftime('%Y-%m-%d %H:%M:%S'))
