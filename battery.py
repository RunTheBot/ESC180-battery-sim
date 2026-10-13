INITIAL_TEMP = 20  # degrees Celsius
INITIAL_CHARGE = 50  # percentage points
INITIAL_TIME = 0  # minutes
INITIAL_BATTERY_HEALTH = True

MIN_TEMP = 0
MIN_CHARGE = 0
MIN_DURATION = 0
HEALTHY_MAX_CAPACITY = 100
UNHEALTHY_MAX_CAPACITY = 80

FAST_CHARGE_MAX_TEMP = 40
FAST_CHARGE_MAX_CHARGE = 80
FAST_CHARGE_RATE = 3  # percentage points per minute
SLOW_CHARGE_RATE = 1  # percentage points per minute
USE_DISCHARGE_RATE = 2  # percentage points per minute
IDLE_DISCHARGE_RATE = 0.5  # percentage points per minute

FAST_CHARGE_HEATING_RATE = 0.5  # degrees Celsius per minute
SLOW_CHARGE_HEATING_RATE = 0.25  # degrees Celsius per minute
USE_HEATING_RATE = 1  # degrees Celsius per minute
COOLING_RATE = 1  # degrees Celsius per minute, idle or after the battery dies

OVERCHARGE_THRESHOLD = 90  # percentage points
OVERCHARGE_WINDOW = 360  # minutes
OVERCHARGE_EVENT_LIMIT = 3

def initialize():
    '''Initializes the global variables needed for the simulation.
    Note: this function is incomplete, and you may want to modify it.
    '''
    global cur_temp # in degrees Celsius
    global cur_charge # in percentage points
    global elapsed_minutes # in minutes
    global is_battery_healthy
    global max_capacity
    global overcharge_events

    cur_temp = INITIAL_TEMP
    cur_charge = INITIAL_CHARGE
    elapsed_minutes = INITIAL_TIME
    is_battery_healthy = INITIAL_BATTERY_HEALTH
    max_capacity = HEALTHY_MAX_CAPACITY
    overcharge_events = []

# Indices for the delta array
TIME = 0
CHARGE = 1
TEMP = 2

# Returns the maximum amount of time (in minutes) that fast charging is possible.
# Also returns the corresponding charge gain and temperature change.
def calculate_max_fast_charge():
    # Charges 3% per minute
    # Fast charging requirements:
    # 1. 0-40C
    # 2. 0-80% charge
    # 3. Good battery health
    if not is_battery_healthy: #Requirement #3
        return (MIN_DURATION, MIN_CHARGE, MIN_TEMP)

    # Fast-charging duration times the charge rate gives the charge gain.
    # Fast-charging duration times the heating rate gives the temperature change.
    # Find which limit is reached first.
    minutes_until_temperature_limit = (FAST_CHARGE_MAX_TEMP - cur_temp) / FAST_CHARGE_HEATING_RATE
    minutes_until_charge_limit = (FAST_CHARGE_MAX_CHARGE - cur_charge) / FAST_CHARGE_RATE
    time_max = max(MIN_DURATION, min(minutes_until_temperature_limit, minutes_until_charge_limit))
    return (time_max, time_max * FAST_CHARGE_RATE, time_max * FAST_CHARGE_HEATING_RATE)

def check_battery_health(time):
    global is_battery_healthy, cur_charge, max_capacity
    # if the battery has been overcharged 3 times in the past 6 hours, the battery is no longer healthy
    # 6 hours = 360 minutes
    recent_overcharge_count = 0 # Counter: number of overcharges that have occurred
    for event in overcharge_events:
        if time - event < OVERCHARGE_WINDOW:
            recent_overcharge_count += 1
    if recent_overcharge_count >= OVERCHARGE_EVENT_LIMIT:
        is_battery_healthy = False
        max_capacity = UNHEALTHY_MAX_CAPACITY

# present tense use
def calculate_battery_use(minutes):
    # Uses 2% per minute
    # Temperature increases by 1C per minute

    # [minutes used, charge change during activity, temperature change during activity]
    delta = [minutes, -minutes * USE_DISCHARGE_RATE, minutes * USE_HEATING_RATE]

    # check if the battery will die
    if -delta[CHARGE] > cur_charge: # If the activity requires more charge than is available, the battery will die.
        time_in_use = cur_charge / USE_DISCHARGE_RATE #amount of time until battery dies
        delta[TEMP] = time_in_use * USE_HEATING_RATE - (minutes - time_in_use) * COOLING_RATE
        # Heating during use minus cooling during the time left.

    return delta

def calculate_idle(minutes):
    # Uses 0.5% per minute
    # Temperature decreases by 1C per minute
    return (minutes, -minutes * IDLE_DISCHARGE_RATE, -minutes * COOLING_RATE)
    # (minutes idle, charge change while idle, temperature change while idle)

def calculate_charge(total_time):
    global cur_charge, max_capacity, is_battery_healthy
    # Fast charge until a limit is reached or the requested time runs out.
    max_fast_charge_minutes, max_fast_charge_gain, fast_temp_max = calculate_max_fast_charge()


    if total_time <= max_fast_charge_minutes:
        return (total_time, total_time * FAST_CHARGE_RATE, total_time * FAST_CHARGE_HEATING_RATE) #Fast charge
    else:
        # slow charge the rest of the time
        slow_charge_time = total_time - max_fast_charge_minutes
        slow_charge = slow_charge_time * SLOW_CHARGE_RATE
        slow_temp = slow_charge_time * SLOW_CHARGE_HEATING_RATE

        # ensure we don't charge past max charge
        if (slow_charge + cur_charge + max_fast_charge_gain > max_capacity):
            charge_after_fast_charging = cur_charge + max_fast_charge_gain
            remaining_capacity = max(MIN_CHARGE, max_capacity - charge_after_fast_charging)
            slow_charge = min(slow_charge, remaining_capacity)

        # Overcharge logic
        # Defined as when the battery is charged to 90% or above.

        minutes_until_overcharge = max(MIN_CHARGE, OVERCHARGE_THRESHOLD - cur_charge - max_fast_charge_gain) / SLOW_CHARGE_RATE
        # Only check while the battery is healthy because the transition needs special handling.
        if slow_charge_time >= minutes_until_overcharge and is_battery_healthy:
            overcharge_events.append(elapsed_minutes + minutes_until_overcharge + max_fast_charge_minutes)
            check_battery_health(elapsed_minutes + minutes_until_overcharge + max_fast_charge_gain)
            # This transition logic should run only once, when battery health changes.
            # It clamps the charge to 90%.
           
            # Unhealthy batteries cannot charge past 80%. When the battery first becomes unhealthy, it will not charge further until discharged below 80%.
            if not is_battery_healthy:
                slow_charge = minutes_until_overcharge * SLOW_CHARGE_RATE
                # If the battery becomes unhealthy, stop charging.


        return (max_fast_charge_minutes + slow_charge_time, max_fast_charge_gain + slow_charge, fast_temp_max + slow_temp)
    # (total time, total charge, total temp) --> so far

def apply_activity(duration, charge, temp):
    global cur_temp
    global cur_charge
    global elapsed_minutes

    cur_temp += temp
    cur_charge += charge
    elapsed_minutes += duration

    # clamp to ensure charge and temp are within bounds
    cur_charge = max(MIN_CHARGE, cur_charge)
    cur_temp = max(MIN_TEMP, cur_temp)
    


# Slow charging is 
def simulate_activity(activity, duration):
    global cur_charge
    if activity == "charge":
        apply_activity(*calculate_charge(duration))
    elif activity == "use":
        apply_activity(*calculate_battery_use(duration))
    elif activity == "idle":
        apply_activity(*calculate_idle(duration))
    else:
        return

# --- getters ---
def duration_fast_charge_possible():
    return calculate_max_fast_charge()[TIME]

def get_cur_temp():
    return cur_temp

def get_cur_charge():
    return cur_charge

def get_cur_battery_health():
    return is_battery_healthy


# --- time prediction stuff ---

def charge_time_needed(minutes):
    # Returns the time needed to charge the battery for use in minutes
    percentage_needed = minutes * USE_DISCHARGE_RATE
    charge_needed = percentage_needed - cur_charge

    if charge_needed <= MIN_CHARGE:
        return MIN_DURATION
    if percentage_needed > max_capacity:
        return None
    return calculate_charge_time(charge_needed)


def calculate_charge_time(charge_needed):
    # Returns the time needed to charge the battery for use in minutes
    if charge_needed <= MIN_CHARGE:
        return MIN_DURATION

    max_fast_charge_minutes, max_fast_charge_gain, fast_temp_max = calculate_max_fast_charge()
    if charge_needed <= max_fast_charge_gain:  # charge needed <= fast charge limit
        return charge_needed / FAST_CHARGE_RATE  # Time needed to obtain the required charge using fast charging.
    else:
        # slow charge the rest of the time
        slow_charge_needed = charge_needed - max_fast_charge_gain
        slow_charge_time = slow_charge_needed / SLOW_CHARGE_RATE
        # Overcharge logic

        minutes_until_overcharge = max(MIN_CHARGE,
                                       OVERCHARGE_THRESHOLD - cur_charge - max_fast_charge_gain) / SLOW_CHARGE_RATE
        # Only check while the battery is healthy because the transition needs special handling.
        if slow_charge_time > minutes_until_overcharge and is_battery_healthy:
            time = elapsed_minutes + minutes_until_overcharge + max_fast_charge_gain
            recent_overcharge_count = 0
            for event in overcharge_events:
                if time - event < OVERCHARGE_WINDOW:
                    recent_overcharge_count += 1
            if recent_overcharge_count >= OVERCHARGE_EVENT_LIMIT - 1:
                return None

        return max_fast_charge_minutes + slow_charge_time


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

    # Edge case: we will reach an overcharge, so we stop at 90%.
    print("This should be none:", charge_time_needed(50))

    # NOOOOOOO
    simulate_activity("charge",80)
    print(get_cur_charge()) # 90
    print(get_cur_temp()) # 22.5
    print(get_cur_battery_health()) # False

    # print("look here")

    # edge case charge above max
    simulate_activity("charge",80)
    print(get_cur_charge()) # 90

    simulate_activity("use",40)
    print(get_cur_charge()) # 10
    print(get_cur_temp()) # 62.5

    simulate_activity("charge",80)
    print(get_cur_charge()) # 80
    print(get_cur_temp()) # 82.5

    initialize()
    # add your tests here

    # Edge case: the battery becomes unhealthy but needs a charge above 90%, such as 100% for 50 minutes of use.
