#!/usr/bin/env python3
"""
JM外呼话术生成器 - 活动信息提取与确认工具
严格的流程：提取活动信息 → 用户确认 → 再生成话术
"""

import json
import re
from typing import Dict, List, Tuple

class ActivityInfoExtractor:
    """活动信息提取器"""
    
    def __init__(self):
        self.required_fields = {
            "brand": "品牌名称",
            "store": "店铺名称",
            "products": "产品名称列表",
            "activity_name": "活动名称",
            "benefits": "权益信息（优惠券/红包/价格等）"
        }
        
        self.optional_fields = {
            "activity_time": "活动时间",
            "industry": "行业类型",
            "pet_type": "宠物类型（如果是宠物行业）"
        }
    
    def extract_from_text(self, text: str) -> Dict:
        """
        从用户提供的活动信息文本中提取关键信息
        
        Args:
            text: 用户提供的活动信息文本
        
        Returns:
            提取的结构化信息
        """
        extracted = {
            "场景识别": [],
            "品牌信息": [],
            "产品信息": [],
            "权益信息": [],
            "时间信息": [],
            "行业判断": [],
            "缺失信息": []
        }
        
        # 分割多个场景
        scenarios = self._split_scenarios(text)
        
        results = []
        for i, scenario_text in enumerate(scenarios, 1):
            scenario_info = self._extract_single_scenario(scenario_text, i)
            results.append(scenario_info)
        
        return {
            "场景数量": len(scenarios),
            "各场景详情": results,
            "提取结果": extracted
        }
    
    def _split_scenarios(self, text: str) -> List[str]:
        """分割多个场景"""
        # 使用"场景X"作为分隔符
        pattern = r'场景[一二三四五六七八九十\d]+[:：]'
        scenarios = re.split(pattern, text)
        # 第一个元素通常是空字符串或前缀文字
        scenarios = [s.strip() for s in scenarios if s.strip()]
        return scenarios
    
    def _extract_single_scenario(self, text: str, scenario_num: int) -> Dict:
        """提取单个场景的信息"""
        info = {
            "场景编号": scenario_num,
            "原始文本": text[:200] + "..." if len(text) > 200 else text,
            "提取结果": {}
        }
        
        # 1. 行业判断
        if any(kw in text for kw in ["猫粮", "猫条", "犬粮", "宠物", "毛孩子"]):
            info["提取结果"]["行业类型"] = "宠物食品"
            if "犬" in text or "狗" in text:
                info["提取结果"]["宠物类型"] = "犬"
            elif "猫" in text:
                info["提取结果"]["宠物类型"] = "猫"
        elif any(kw in text for kw in ["垃圾袋", "T恤", "日用品"]):
            info["提取结果"]["行业类型"] = "日用品"
        else:
            info["提取结果"]["行业类型"] = "未知"
        
        # 2. 品牌信息提取
        brand_patterns = [
            r'网易天成',
            r'京东',
            r'三拼鸭肉梨',
            r'鲜蒸猫粮',
            r'(\w+)京东自营旗舰店',
        ]
        
        brands_found = []
        for pattern in brand_patterns:
            matches = re.findall(pattern, text)
            brands_found.extend(matches)
        
        if brands_found:
            info["提取结果"]["品牌名称"] = brands_found[0] if len(set(brands_found)) == 1 else f"多个品牌: {', '.join(set(brands_found))}"
        else:
            info["提取结果"]["品牌名称"] = "⚠️ 未识别，需要用户补充"
        
        # 3. 店铺名称提取
        store_pattern = r'(\w+京东自营旗舰店|京东自营)'
        store_matches = re.findall(store_pattern, text)
        if store_matches:
            info["提取结果"]["店铺名称"] = store_matches[0]
        else:
            info["提取结果"]["店铺名称"] = "京东自营旗舰店（默认）"
        
        # 4. 产品信息提取
        products = []
        product_patterns = [
            r'(\d+(?:\.\d+)?kg[^，。\n]+(?:猫粮|犬粮|垃圾袋|T恤))',
            r'((?:全价|鲜蒸)[^，。\n]+(?:猫粮|犬粮))',
            r'(厨房专用[^，。\n]+垃圾袋)',
            r'(\d+A抗菌[^，。\n]+T恤)',
            r'(三拼鸭肉梨[^，。\n]+款)',
        ]
        
        for pattern in product_patterns:
            matches = re.findall(pattern, text)
            products.extend(matches)
        
        if products:
            info["提取结果"]["产品名称"] = list(set(products))
        else:
            info["提取结果"]["产品名称"] = ["⚠️ 未识别，需要用户补充"]
        
        # 5. 权益信息提取
        benefits = {}
        
        # 优惠券
        coupon_patterns = [
            r'(\d+元直减红包)',
            r'(\d+-\d+元?(?:大促)?券)',
            r'(无门槛\d折券)',
            r'(\d+-\d+红包)',
        ]
        for pattern in coupon_patterns:
            matches = re.findall(pattern, text)
            if matches:
                benefits["优惠券/红包"] = list(set(matches))
        
        # 价格信息
        price_patterns = [
            r'((?:券后|红包后|到手)[^\n]{0,30}\d+(?:\.\d+)?元)',
            r'((?:台前价|原价)\d+(?:\.\d+)?元)',
        ]
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            if matches:
                benefits["价格信息"] = list(set(matches))
        
        # 赠品
        gift_pattern = r'(\d+件好礼|赠送[^，。\n]+)'
        gift_matches = re.findall(gift_pattern, text)
        if gift_matches:
            benefits["赠品"] = list(set(gift_matches))
        
        info["提取结果"]["权益信息"] = benefits if benefits else "⚠️ 未识别完整，需要人工确认"
        
        # 6. 时间信息
        time_pattern = r'(\d+\.\d+-\d+\.\d+)'
        time_matches = re.findall(time_pattern, text)
        if time_matches:
            info["提取结果"]["活动时间"] = time_matches[0]
        else:
            info["提取结果"]["活动时间"] = "未配置"
        
        # 7. 缺失信息检查
        missing = []
        if "⚠️" in info["提取结果"].get("品牌名称", ""):
            missing.append("品牌名称")
        if "⚠️" in str(info["提取结果"].get("产品名称", [])):
            missing.append("产品名称")
        if not info["提取结果"].get("权益信息") or "⚠️" in str(info["提取结果"].get("权益信息", "")):
            missing.append("完整权益信息")
        
        info["缺失信息"] = missing if missing else ["无缺失"]
        
        return info
    
    def format_for_confirmation(self, extraction_result: Dict) -> str:
        """
        格式化提取结果，用于用户确认
        
        Args:
            extraction_result: 提取的结果
        
        Returns:
            格式化的确认文本
        """
        output = []
        output.append("=" * 80)
        output.append("活动信息提取结果 - 请确认")
        output.append("=" * 80)
        output.append("")
        
        for i, scenario in enumerate(extraction_result["各场景详情"], 1):
            output.append(f"【场景{i}】")
            output.append("-" * 80)
            
            result = scenario["提取结果"]
            
            # 品牌信息
            brand = result.get("品牌名称", "")
            brand_icon = "✅" if "⚠️" not in str(brand) else "❌"
            output.append(f"{brand_icon} 品牌名称: {brand}")
            
            # 店铺信息
            store = result.get("店铺名称", "")
            output.append(f"✅ 店铺名称: {store}")
            
            # 产品信息
            products = result.get("产品名称", [])
            product_icon = "✅" if all("⚠️" not in str(p) for p in products) else "❌"
            output.append(f"{product_icon} 产品名称: {', '.join(products) if isinstance(products, list) else products}")
            
            # 行业类型
            industry = result.get("行业类型", "")
            output.append(f"✅ 行业类型: {industry}")
            
            # 宠物类型
            pet_type = result.get("宠物类型", "")
            if pet_type:
                output.append(f"✅ 宠物类型: {pet_type}")
            
            # 权益信息
            benefits = result.get("权益信息", {})
            benefits_icon = "✅" if benefits and "⚠️" not in str(benefits) else "⚠️"
            output.append(f"{benefits_icon} 权益信息:")
            if isinstance(benefits, dict):
                for key, value in benefits.items():
                    output.append(f"   - {key}: {value}")
            else:
                output.append(f"   {benefits}")
            
            # 活动时间
            time_info = result.get("活动时间", "")
            time_icon = "✅" if time_info != "未配置" else "⚠️"
            output.append(f"{time_icon} 活动时间: {time_info}")
            
            # 缺失信息
            missing = scenario.get("缺失信息", [])
            if missing and missing != ["无缺失"]:
                output.append("")
                output.append("⚠️  缺失信息:")
                for m in missing:
                    output.append(f"   - {m}")
            
            output.append("")
        
        output.append("=" * 80)
        output.append("请确认以上信息是否正确：")
        output.append("")
        output.append("✅ 如果信息正确，请回复'确认'，我将开始生成话术")
        output.append("❌ 如果有错误或缺失，请补充正确的活动信息")
        output.append("")
        output.append("⚠️  注意：场景中有 ❌ 标记的项目为必填项，请务必补充完整")
        output.append("=" * 80)
        
        return "\n".join(output)

def main():
    """测试活动信息提取"""
    # 示例活动信息
    sample_text = """
    活动信息：
    场景一：
    5元直减红包，有效期4.6-4.11
    10周年大促券：200-30，红包叠券200-35
    厨房专用特厚抽绳垃圾袋：3卷60只14.9，红包后9.9
    10A抗菌纯棉T恤，99元任选3件，红包后94元3件

    场景二：
    宠物无门槛8折券、299-45红包、599-90红包
    网易天成 全价冻干双拼猫粮3.0：1.8kg*4袋 台前价339，券后271.2
    全价冻干双拼猫粮兔肉美毛款：1.5kg*4 台前价329，券后263.2
    能用券不一定能用红包，只说8折券后价

    场景三：
    3D乳化鲜蒸科技100%纯鲜肉，全价鲜蒸猫粮买4袋叠券后到手476元，一次带走19件
    (同款试吃装50g*4+猫抓板*1+鲜蒸猫条*2+鲜蒸猫饭6+鲜蒸罐头*6罐)
    宠物单笔实付满239元加赠宠物除臭香氛

    场景四：
    三拼鸭肉梨新品浓汤款4袋叠198-30元老客券，到手262元，折合65.5/袋
    再加赠14件好礼-鸭肉梨试吃120g*3+犬用膳食罐100g*6+鲜蒸犬饭70g*3+犬用湿巾80抽+超满足冻干桶2.0袋装50g
    宠物单笔实付满239元加赠宠物除臭香氛
    """
    
    extractor = ActivityInfoExtractor()
    result = extractor.extract_from_text(sample_text)
    confirmation_text = extractor.format_for_confirmation(result)
    
    print(confirmation_text)

if __name__ == "__main__":
    main()