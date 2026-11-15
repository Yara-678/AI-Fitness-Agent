import json

def get_food_info(food_name):
    try:
        with open("food_data.json", "r", encoding="utf-8") as f:
            food_db = json.load(f)
        if food_name in food_db:
            data = food_db[food_name]
            return f"【来自本地数据库】每100g {food_name}：热量{data['calories']}大卡。"
        return "未找到该食物。"
    except:
        return "读取食物库失败。"

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
    
    return f"【来自本地计算器】进行{duration_min}分钟的{exercise_type}（系统默认坡度{incline}，速度{speed}），大约消耗 {calories:.0f} 大卡。"