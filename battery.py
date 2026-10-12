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

def simulate_activity(activity, duration):
    global cur_charge 
    if activity == "charge": 
        apply_activity (*calculate_charge(duration)) 
    elif activity == "use": 
        apply_activity (*calculate_use(duration)) 
    elif activity == "idle": 
        apply_activity (*calculate_idle(duration))
    else: 
        return 

def apply_activity (duration, charge, temp): 
    global cur_temp 
    global cur_charge 
    global cur_time 

    cur_temp = temp 
    cur_charge = charge 
    cur_time += duration 

def get_cur_temp():
    return cur_temp 

def get_cur_charge():
    return cur_charge 

def get_cur_battery_health():
    return good_battery_health 

def charge_time_needed(minutes):
    global cur_charge 
    global max_capacity 
    global good_battery_health 
    global fast_charge_max 
    global slow_charge 
    global slow_temp 
    #Fast charge till max or we hit out time max 
    fast_charge_max = duration_fast_charge_possible() 

    if (minutes > 50) or (good_battery_health == False and minutes > 40): 
        return -1 
    
    charge_needed = minutes * 2 
    if (cur_charge >= charge_needed): 
        return (0) 
    else: 
        if (charge_needed < cur_charge + fast_charge_max * 3): 
            return ((charge_needed - cur_charge)/ 3) 
        else: 
            return (fast_charge_max + (charge_needed - fast_charge_max * 3 - cur_charge)) 
        

def duration_fast_charge_possible(): 
    global cur_temp 
    global cur_charge 
    global time_temp_max 
    global time_charge_max 
    global time_max 

    #Charges 3% per minute 
    #Fast charging requirements: 
    #1. 0-40C 
    #2. 0-80% charge 
    #3. Good battery health 

    if not good_battery_health: #Requirement #3 
        return (0) 

    #time_limit*3 --> How much more CHARGE intil limit is reached 
    #time_limit*0.5 --> how much more TEMP until limit is reached 
    #Find which max is reached first 
    
    time_temp_max = (40 - cur_temp) / 0.5 
    time_charge_max = (80 - cur_charge) / 3 
    time_max = max(0, min(time_temp_max , time_charge_max)) 
    return (time_max) 

def calculate_charge(total_time): 
    global cur_charge 
    global max_capacity 
    global good_battery_health 
    global fast_charge_max 
    global slow_charge 
    global slow_temp 
    #Fast charge till max or we hit out time max 
    fast_charge_max = duration_fast_charge_possible() 

    if total_time <= fast_charge_max: 
        return (total_time, cur_charge + total_time * 3, cur_temp + total_time * 0.5) #Fast charge 

    else: 
        #Slow charge the rest of hte time 
        slow_charge_time = total_time - fast_charge_max  
        slow_charge = slow_charge_time * 1 
        slow_temp = slow_charge_time * 0.25 

    
    if not good_battery_health: 
            max_capacity = 80 
    else: 
        max_capacity = 100 

    if (cur_charge + fast_charge_max * 3 + slow_charge > 90): 
        overcharge_events.append(cur_time + total_time)

    if (len(overcharge_events) - 1) >= 2 and good_battery_health: 
        if (overcharge_events[len(overcharge_events) -1] - overcharge_events[len(overcharge_events) -3]) <= 360: 
            good_battery_health = False 
            max_capacity = 90 

    return (total_time, min(max_capacity, cur_charge + fast_charge_max * 3 + slow_charge), cur_temp + fast_charge_max * 0.5 + slow_charge_time * 0.25)


#USAGE 
# - Usage discharges hte battery by 2% per minute 
# - Temperature increase by 1C per minute during usage 
# - min 0% 
# - min 0 degree 

def calculate_use(use_minutes): 
    #Uses 2% per minute 
    #Temperature increases by 1C per minute 

    mins_to_death = cur_charge / 2 
    mins_after_death = use_minutes - mins_to_death 

    if (cur_charge >= use_minutes * 2): 
        return (use_minutes, max (0, cur_charge - use_minutes * 2), max (0, cur_temp + use_minutes * 1)) 
    else: 
        return (use_minutes, 0, max (0, cur_temp + mins_to_death * 1 - mins_after_death * 1)) 
#IDLE 
# - Discharges the battery by 0.5% per minute 
# - Decreases the temperature by 1C per minute 
# - Min temp is 0 

def calculate_idle (idle_minutes): 
    # Uses 0.5% per minute 
    # Temperature decreases by 1C per minute 

    return (idle_minutes, max(0, cur_charge - idle_minutes * 0.5), max(0, cur_temp - idle_minutes * 1)) 


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
    # # # add your tests here
    print(duration_fast_charge_possible()) 
    print(charge_time_needed(50)) 
    simulate_activity("use",200)
    print(get_cur_charge())  
    print(get_cur_temp())  





