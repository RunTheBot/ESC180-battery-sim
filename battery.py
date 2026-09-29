def initialize():
    '''Initializes the global variables needed for the simulation.
    Note: this function is incomplete, and you may want to modify it.
    '''
    global cur_temp # in degrees Celsius
    global cur_charge # in percentage points
    global cur_time # in minutes
    global good_battery_health
    global max_capacity
    global overcharge_events

    cur_temp = 20
    cur_charge = 50
    cur_time = 0
    good_battery_health = True
    max_capacity = 100
    overcharge_events = []

TIME = 0
CHARGE = 1
TEMP = 2

# Returns the max ammount of time (in minutes) that fast charging is possible
# Also returns how much charge that would be and delta temp
def calculate_max_fast_charge():
    # Charges 3% per minute
    # Fast charging requirements:
    # 1. 0-40C
    # 2. 0-80% charge
    # 3. Good battery health
    if not good_battery_health:
        return (0, 0, 0)
    # find which limit is reached first
    time_temp_limit = (40 - cur_temp) / 0.5
    time_charge_limit = (80 - cur_charge) / 3
    time_limit = max(0, min(time_temp_limit, time_charge_limit))
    return (time_limit, time_limit * 3, time_limit * 0.5)

def check_battery_health(time):
    global good_battery_health, cur_charge, max_capacity
    # if the battery has been overcharged 3 times in the past 6 hours, the battery is no longer healthy
    # 6 hours = 360 minutes
    overcharges_in_range = 0
    for event in overcharge_events:
        if time - event < 360:
            overcharges_in_range += 1
    if overcharges_in_range >= 3:
        good_battery_health = False
        max_capacity = 80

def calculate_use(minutes):
    # Uses 2% per minute
    # Temperature increases by 1C per minute

    delta = [minutes, minutes * -2, minutes * 1]

    # check if the battery will die
    if -delta[CHARGE] > cur_charge:
        time_in_use = cur_charge/2
        delta[TEMP] = time_in_use-(minutes-time_in_use)

    return delta

def calculate_idle(minutes):
    # Uses 0.5% per minute
    # Temperature decreases by 1C per minute
    return (minutes, minutes * -0.5, minutes * -1)

def calculate_charge(total_time):
    global cur_charge, max_capacity
    # Fast charge till max or we hit out time limit
    fast_time_limit, fast_charge_limit, fast_temp_limit = calculate_max_fast_charge()

    if total_time <= fast_time_limit:
        return (total_time, total_time * 3, total_time * 0.5)
    else:
        # slow charge the rest of the time
        slow_charge_time = total_time - fast_time_limit
        slow_charge = slow_charge_time
        slow_temp = slow_charge_time * 0.25

        # ensure we don't charge past max charge
        if (slow_charge + cur_charge + fast_charge_limit > max_capacity):
            slow_charge += max_capacity - (slow_charge + cur_charge + fast_charge_limit)

        # Overcharge logic
        # Define as when the battery is charged beyond 90% (inclusive)

        time_till_overcharge = (90 - cur_charge-fast_charge_limit)
        if slow_charge_time >= time_till_overcharge:
            overcharge_events.append(cur_time + time_till_overcharge)
            check_battery_health(cur_time + time_till_overcharge)

        return (fast_time_limit + slow_charge_time, fast_charge_limit + slow_charge, fast_temp_limit + slow_temp)

def calculate_charge_time(charge_needed):
    # Returns the time needed to charge the battery for use in minutes
    if charge_needed <= 0:
        return 0

    time_limit, charge_limit, temp_limit = calculate_max_fast_charge()
    if charge_needed <= charge_limit:
        return charge_needed / 3
    else:
        # slow charge the rest of the time
        slow_charge_needed = charge_needed - charge_limit
        slow_charge_time = slow_charge_needed
        return time_limit + slow_charge_time

def apply_activity(duration, charge, temp):
    global cur_temp
    global cur_charge
    global cur_time

    cur_temp += temp
    cur_charge += charge
    cur_time += duration

    # clap to ensure charge and temp are within bounds
    cur_charge = max(0, cur_charge)
    cur_temp = max(0, cur_temp)
    


# Slow charging is 
def simulate_activity(activity, duration):
    global cur_charge
    if activity == "charge":
        apply_activity(*calculate_charge(duration))
    elif activity == "use":
        apply_activity(*calculate_use(duration))
    elif activity == "idle":
        apply_activity(*calculate_idle(duration))
    else:
        return

def duration_fast_charge_possible():
    return calculate_max_fast_charge()[TIME]

def get_cur_temp():
    return cur_temp

def get_cur_charge():
    return cur_charge

def get_cur_battery_health():
    return good_battery_health

def charge_time_needed(minutes):
    # Returns the time needed to charge the battery for use in minutes
    percentage_needed = minutes * 2
    charge_needed = percentage_needed - cur_charge

    if percentage_needed > max_capacity:
        return None
    if charge_needed <= 0:
        return 0
    return calculate_charge_time(charge_needed)

    

if __name__ == '__main__':
    initialize()

    print(duration_fast_charge_possible()) # 10
    print(charge_time_needed(50)) # 30

    simulate_activity("charge",30)
    print(get_cur_charge()) # 100
    print(get_cur_temp()) # 30

    simulate_activity("use",50)
    print(get_cur_charge()) # 0
    print(get_cur_temp()) # 80

    simulate_activity("use",10)
    print(get_cur_charge()) # 0
    print(get_cur_temp()) # 70

    simulate_activity("charge",100)
    print(get_cur_charge()) # 100
    print(get_cur_temp()) # 95

    simulate_activity("idle",100)
    print(get_cur_charge()) # 50
    print(get_cur_temp()) # 0
    print(get_cur_battery_health()) # True
    print(duration_fast_charge_possible()) # 10

    # NOOOOOOO
    simulate_activity("charge",80)
    print(get_cur_charge()) # 90
    print(get_cur_temp()) # 22.5
    print(get_cur_battery_health()) # False

    simulate_activity("use",40)
    print(get_cur_charge()) # 10
    print(get_cur_temp()) # 62.5

    simulate_activity("charge",80)
    print(get_cur_charge()) # 80
    print(get_cur_temp()) # 82.5

    initialize()
    # add your tests here
