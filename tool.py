# 工具：计算运动消耗热量
def calc_exercise_calories(exercise_type, duration_min, weight, incline=0, speed=0):
    # 强制识别：只要带了跑步/爬坡字眼，直接给高强度基础值
    if "跑步" in exercise_type or "爬坡" in exercise_type or "running" in exercise_type.lower():
        # 如果大模型没传速度或坡度，默认按 4.8 和 12 度算（防止它偷懒）
        if speed == 0: speed = 4.8
        if incline == 0: incline = 12
        
        # 坡度每增加1%，METs 增加 0.1
        base_mets = 6.0 if speed < 5 else 8.0
        mets = base_mets + (incline * 0.1)
    elif "力量" in exercise_type or "举铁" in exercise_type:
        mets = 5.0
    else:
        mets = 4.0
        
    calories = mets * weight * (duration_min / 60)
    
    return f"【来自本地计算器】根据你的体重（{weight}kg）和运动参数（{exercise_type}，坡度{incline}，速度{speed}），进行{duration_min}分钟，大约消耗 {calories:.0f} 大卡。"