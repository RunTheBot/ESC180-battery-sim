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

#for delta array 
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
    if not good_battery_health: #Requirement #3 
        return (0, 0, 0)

    #time_limit *3 --> how much more charge until limit is reached 
    #time_limi * 0.5 --> how much more temperature until limit is reached 
    # find which max is reached first
    time_temp_max = (40 - cur_temp) / 0.5
    time_charge_max = (80 - cur_charge) / 3
    time_max = max(0, min(time_temp_max, time_charge_max))
    return (time_max, time_max * 3, time_max * 0.5)

def check_battery_health(time):
    global good_battery_health, cur_charge, max_capacity
    # if the battery has been overcharged 3 times in the past 6 hours, the battery is no longer healthy
    # 6 hours = 360 minutes
    overcharges_in_range = 0 #Counter --> number of overcharges that has occurred 
    for event in overcharge_events:
        if time - event < 360:
            overcharges_in_range += 1
    if overcharges_in_range >= 3:
        good_battery_health = False
        max_capacity = 80
# present tense use
def calculate_battery_use(minutes):
    # Uses 2% per minute
    # Temperature increases by 1C per minute

    #[amount of minutes used, amount charge has decreased during acitity, amount temperature as increase during acitivty]
    delta = [minutes, minutes * -2, minutes * 1]

    # check if the battery will die
    if -delta[CHARGE] > cur_charge: #If the amount of charge that the acitivty will result in is more than the battery we have, the battery will die 
        time_in_use = cur_charge/2 #amount of time until battery dies  
        delta[TEMP] = time_in_use-(minutes-time_in_use) 
        #amount of time used - (amount of time left) 

    return delta

def calculate_idle(minutes):
    # Uses 0.5% per minute
    # Temperature decreases by 1C per minute
    return (minutes, minutes * -0.5, minutes * -1)
    #(minutes idle, amount temp decrease while idle, amount temp decreased while idle)

def calculate_charge(total_time):
    global cur_charge, max_capacity, good_battery_health
    # Fast charge till max or we hit out time max
    fast_time_max, fast_charge_max, fast_temp_max = calculate_max_fast_charge()


    if total_time <= fast_time_max:
        return (total_time, total_time * 3, total_time * 0.5) #Fast charge
    else:
        # slow charge the rest of the time
        slow_charge_time = total_time - fast_time_max
        slow_charge = slow_charge_time
        slow_temp = slow_charge_time * 0.25

        # ensure we don't charge past max charge
        if (slow_charge + cur_charge + fast_charge_max > max_capacity):
            slow_charge += max(-slow_charge, max_capacity - (slow_charge + cur_charge + fast_charge_max))

        # Overcharge logic
        # Define as when the battery is charged beyond 90% (inclusive)

        time_till_overcharge = max(0, 90 - cur_charge - fast_charge_max)
        # Only check when we have good battery health cuz transition has weird logic
        if slow_charge_time >= time_till_overcharge and good_battery_health:
            overcharge_events.append(cur_time + time_till_overcharge + fast_charge_max)
            check_battery_health(cur_time + time_till_overcharge + fast_charge_max)
            # weird transition logic only every should be hit once on trasition
            # it basically clamps the value to 90
           
           # Batteries in bad health state cannot charge past 80%. If the battery initially switches to a bad health state, it will not charge further until discharged below 80%.
            if not good_battery_health:
                slow_charge = time_till_overcharge 
                #if we hit bad battery health, stop charging 


        return (fast_time_limit + slow_charge_time, fast_charge_limit + slow_charge, fast_temp_limit + slow_temp)
    # (total time, total charge, total temp) --> so far 

def calculate_charge_time(charge_needed):
    # Returns the time needed to charge the battery for use in minutes
    if charge_needed <= 0:
        return 0

    time_limit, charge_limit, temp_limit = calculate_max_fast_charge()
    if charge_needed <= charge_limit: #charge needed <= fast charge limit 
        return charge_needed / 3 #amount of charge needed until until slow charge 
    else:
        # slow charge the rest of the time
        slow_charge_needed = charge_needed - fast_charge_max
        slow_charge_time = slow_charge_needed
        # Over charge logic

        time_till_overcharge = max(0, 90 - cur_charge - fast_charge_max)
        # Only check when we have good battery health cuz transition has weird logic
        if slow_charge_time > time_till_overcharge and good_battery_health:
            time = cur_time + time_till_overcharge + fast_charge_max
            overcharges_in_range = 0
            for event in overcharge_events:
                if time - event < 360:
                    overcharges_in_range += 1
            if overcharges_in_range >= 2:
                return None
        
        return fast_time_max + slow_charge_time
        
        

def apply_activity(duration, charge, temp):
    global cur_temp
    global cur_charge
    global cur_time

    cur_temp += temp
    cur_charge += charge
    cur_time += duration

    # clamp to ensure charge and temp are within bounds
    cur_charge = max(0, cur_charge)
    cur_temp = max(0, cur_temp)
    


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

    # Edge case: we will hit a overchage so we stop at 90
    print("This should be none:", charge_time_needed(50))

    # NOOOOOOO
    simulate_activity("charge",80)
    print(get_cur_charge()) # 90
    print(get_cur_temp()) # 22.5
    print(get_cur_battery_health()) # False

    print("look here")

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

    # Edge case, transition into bad battery state but needs a charge above 90 so like 50 mins battery is at 100%
