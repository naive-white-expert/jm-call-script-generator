#!/usr/bin/env python3
"""
JM外呼话术生成器 - 活动信息提取与确认工具 v2.0
严格按照标准格式提取，缺少任意内容都确认，但支持用户坚持生成
"""

import json
import re
from typing import Dict, List, Tuple, Optional

class ActivityInfoExtractor:
    """活动信息提取器 - 标准格式"""
    
    def extract_from_text(self, text: str) -> Dict:
        """
        从用户提供的活动信息文本中提取关键信息
        
        Args:
            text: 用户提供的活动信息文本
        
        Returns:
            提取的结构化信息
        """
        # 分割多个场景
        scenarios = self._split_scenarios(text)
        
        results = []
        for i, scenario_text in enumerate(scenarios, 1):
            scenario_info = self._extract_single_scenario(scenario_text, i)
            results.append(scenario_info)
        
        return {
            "场景数量": len(scenarios),
            "各场景信息": results
        }
    
    def _split_scenarios(self, text: str) -> List[str]:
        """分割多个场景"""
        pattern = r'场景[一二三四五六七八九十\d]+[:：]'
        scenarios = re.split(pattern, text)
        scenarios = [s.strip() for s in scenarios if s.strip()]
        return scenarios
    
    def _extract_single_scenario(self, text: str, scenario_num: int) -> Dict:
        """提取单个场景的信息 - 按照标准格式"""
        
        info = {
            "场景编号": scenario_num,
            "原始文本": text[:150] + "..." if len(text) > 150 else text
        }
        
        # ==================== 1. 品牌信息 ====================
        brand_info = self._extract_brand_info(text)
        info["品牌信息"] = brand_info
        
        # ==================== 2. 活动信息 ====================
        activity_info = self._extract_activity_info(text)
        info["活动信息"] = activity_info
        
        # ==================== 3. 产品信息 ====================
        product_info = self._extract_product_info(text)
        info["产品信息"] = product_info
        
        # ==================== 4. 利益点信息 ====================
        benefit_info = self._extract_benefit_info(text)
        info["利益点信息"] = benefit_info
        
        # ==================== 5. 场景类型判断 ====================
        scenario_type = self._judge_scenario_type(text, benefit_info, product_info)
        info["场景类型"] = scenario_type
        
        # ==================== 6. 缺失信息汇总 ====================
        missing = self._check_missing_info(info)
        info["缺失信息"] = missing
        info["是否完整"] = len(missing) == 0
        
        return info
    
    def _extract_brand_info(self, text: str) -> Dict:
        """提取品牌信息（品牌名称、店铺名称）"""
        result = {
            "品牌名称": "",
            "店铺名称": ""
        }
        
        # 品牌名称提取规则
        brand_keywords = [
            "网易天成", "京东京造", "网易严选", "皇家", "渴望", 
            "爱肯拿", "巅峰", "GO!", "now", "纽翠斯"
        ]
        
        # 尝试匹配已知品牌
        for brand in brand_keywords:
            if brand in text:
                result["品牌名称"] = brand
                break
        
        # 如果没有匹配到已知品牌，尝试提取
        if not result["品牌名称"]:
            # 尝试提取 "XX京东自营旗舰店" 前的品牌
            brand_pattern = r'(\w{2,8})(?:京东自营旗舰店|京东旗舰店)'
            match = re.search(brand_pattern, text)
            if match:
                result["品牌名称"] = match.group(1)
            else:
                # 尝试提取产品名作为品牌（需要用户确认）
                product_brand_pattern = r'(\w{2,6})(?:猫粮|犬粮|粮)'
                match = re.search(product_brand_pattern, text)
                if match:
                    result["品牌名称"] = f"{match.group(1)}（需确认是否为品牌名）"
                else:
                    result["品牌名称"] = "❌ 未识别，请补充"
        
        # 店铺名称提取
        store_patterns = [
            r'(\w{2,10}京东自营旗舰店)',
            r'(\w{2,10}京东旗舰店)',
            r'京东自营店',
        ]
        
        for pattern in store_patterns:
            match = re.search(pattern, text)
            if match:
                result["店铺名称"] = match.group(0) if hasattr(match, 'group') else match
                break
        
        if not result["店铺名称"]:
            # 如果明确提到了京东，默认为京东自营旗舰店
            if "京东" in text:
                result["店铺名称"] = "京东自营旗舰店（默认）"
            else:
                result["店铺名称"] = "❌ 未识别，请补充"
        
        return result
    
    def _extract_activity_info(self, text: str) -> Dict:
        """提取活动信息（活动名称、活动时间）"""
        result = {
            "活动名称": "",
            "活动时间": ""
        }
        
        # 活动时间提取
        time_patterns = [
            r'有效期(\d+\.\d+-\d+\.\d+)',
            r'(\d+\.\d+-\d+\.\d+)',
            r'(\d+月\d+日?-\d+月?\d+日?)',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                result["活动时间"] = match.group(1)
                break
        
        if not result["活动时间"]:
            result["活动时间"] = "⚠️ 未配置"
        
        # 活动名称提取（根据活动特征推断）
        if "周年" in text:
            match = re.search(r'(\d+周年[^，。\n]*)', text)
            if match:
                result["活动名称"] = match.group(1)
        elif "新品" in text:
            result["活动名称"] = "新品首发活动"
        elif "大促" in text:
            result["活动名称"] = "大促活动"
        else:
            result["活动名称"] = "限时福利活动（默认）"
        
        return result
    
    def _extract_product_info(self, text: str) -> Dict:
        """提取产品信息（主要产品、产品特点）"""
        result = {
            "主要产品": [],
            "产品特点": []
        }
        
        # 产品名称提取
        product_patterns = [
            # 宠物食品
            r'((?:全价|鲜蒸|冻干双拼|三拼)[^，。\n]{0,20}(?:猫粮|犬粮))',
            r'(\d+(?:\.\d+)?kg[^，。\n]{0,15}(?:猫粮|犬粮))',
            # 日用品
            r'(厨房专用[^，。\n]{0,20}垃圾袋)',
            r'(\d+A抗菌[^，。\n]{0,20}T恤)',
            r'(\d+卷\d+只[^，。\n]{0,10}垃圾袋)',
        ]
        
        products = []
        for pattern in product_patterns:
            matches = re.findall(pattern, text)
            products.extend(matches)
        
        if products:
            result["主要产品"] = list(set(products))
        else:
            result["主要产品"] = ["❌ 未识别，请补充"]
        
        # 产品特点提取
        features = []
        
        # 重量/规格
        weight_pattern = r'(\d+(?:\.\d+)?kg\*?\d*袋?)'
        weight_matches = re.findall(weight_pattern, text)
        if weight_matches:
            features.append(f"规格: {', '.join(set(weight_matches))}")
        
        # 特殊卖点
        if "100%纯鲜肉" in text:
            features.append("100%纯鲜肉")
        if "3D乳化鲜蒸科技" in text:
            features.append("3D乳化鲜蒸科技")
        if "抗菌" in text:
            features.append("抗菌材质")
        if "冻干" in text:
            features.append("含冻干")
        
        result["产品特点"] = features if features else ["无特殊卖点"]
        
        return result
    
    def _extract_benefit_info(self, text: str) -> Dict:
        """提取利益点信息（核心权益、价格优势、赠品）"""
        result = {
            "核心权益": [],
            "价格优势": [],
            "赠品": []
        }
        
        # 核心权益提取（优惠券、红包等）
        benefits = []
        
        # 优惠券
        coupon_patterns = [
            r'(\d+元直减红包)',
            r'(\d+-\d+元?(?:大促)?券)',
            r'(无门槛\d折券)',
            r'(\d+-\d+红包)',
            r'(叠\d+-\d+元(?:老客)?券)',
        ]
        
        for pattern in coupon_patterns:
            matches = re.findall(pattern, text)
            benefits.extend(matches)
        
        if benefits:
            result["核心权益"] = list(set(benefits))
        else:
            result["核心权益"] = ["❌ 未识别，请补充"]
        
        # 价格优势提取
        prices = []
        
        # 券后价/到手价
        price_patterns = [
            r'(?:券后|红包后|到手)[^\n]{0,10}?(\d+(?:\.\d+)?元)',
            r'折合(\d+\.\d+)/袋',
            r'(台前价\d+(?:\.\d+)?元)',
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            prices.extend(matches)
        
        if prices:
            result["价格优势"] = list(set(prices))
        else:
            result["价格优势"] = ["无明确价格优势"]
        
        # 赠品提取
        gifts = []
        
        # 赠品数量
        gift_pattern = r'(\d+件(?:好礼|赠品))'
        gift_matches = re.findall(gift_pattern, text)
        if gift_matches:
            gifts.extend(gift_matches)
        
        # 具体赠品
        specific_gifts = [
            r'(猫条)',
            r'(猫抓板)',
            r'(试吃装?[^，。\n]{0,20})',
            r'(宠物除臭香氛)',
        ]
        
        for pattern in specific_gifts:
            matches = re.findall(pattern, text)
            gifts.extend(matches)
        
        if gifts:
            result["赠品"] = list(set(gifts))
        else:
            result["赠品"] = ["无赠品"]
        
        return result
    
    def _judge_scenario_type(self, text: str, benefit_info: Dict, product_info: Dict) -> Dict:
        """判断场景类型（有券/无券、宠物/非宠物、猫粮/犬粮）"""
        result = {
            "优惠券场景": "",
            "行业类型": "",
            "宠物类型": ""
        }
        
        # 判断是否有券
        core_benefits = benefit_info.get("核心权益", [])
        if core_benefits and "❌" not in str(core_benefits):
            result["优惠券场景"] = "有券场景"
        else:
            result["优惠券场景"] = "无券场景"
        
        # 判断行业类型
        if any(kw in text for kw in ["猫粮", "犬粮", "猫条", "猫抓板", "宠物"]):
            result["行业类型"] = "宠物食品"
            
            # 判断宠物类型
            if "犬" in text or "狗" in text:
                result["宠物类型"] = "犬粮"
            elif "猫" in text:
                result["宠物类型"] = "猫粮"
            else:
                result["宠物类型"] = "宠物通用"
        elif any(kw in text for kw in ["垃圾袋", "T恤", "日用品"]):
            result["行业类型"] = "日用品"
            result["宠物类型"] = "非宠物"
        else:
            result["行业类型"] = "未知行业"
            result["宠物类型"] = "非宠物"
        
        return result
    
    def _check_missing_info(self, info: Dict) -> List[str]:
        """检查缺失的信息"""
        missing = []
        
        # 检查品牌信息
        brand_info = info.get("品牌信息", {})
        if "❌" in brand_info.get("品牌名称", ""):
            missing.append("品牌名称")
        if "❌" in brand_info.get("店铺名称", ""):
            missing.append("店铺名称")
        
        # 检查活动信息
        activity_info = info.get("活动信息", {})
        if "⚠️" in activity_info.get("活动时间", ""):
            missing.append("活动时间（可选）")
        
        # 检查产品信息
        product_info = info.get("产品信息", {})
        if any("❌" in p for p in product_info.get("主要产品", [])):
            missing.append("产品名称")
        
        # 检查利益点信息
        benefit_info = info.get("利益点信息", {})
        if any("❌" in b for b in benefit_info.get("核心权益", [])):
            missing.append("核心权益")
        
        return missing
    
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
        output.append("活动信息提取结果 - 请确认后再生成话术")
        output.append("=" * 80)
        output.append("")
        
        for scenario in extraction_result["各场景信息"]:
            scenario_num = scenario["场景编号"]
            output.append(f"【场景{scenario_num}】")
            output.append("-" * 80)
            
            # 1. 品牌信息
            brand_info = scenario.get("品牌信息", {})
            output.append("✦ 品牌信息:")
            brand_name = brand_info.get("品牌名称", "")
            brand_icon = "✅" if "❌" not in brand_name and "需确认" not in brand_name else "❌"
            output.append(f"  {brand_icon} 品牌名称: {brand_name}")
            
            store_name = brand_info.get("店铺名称", "")
            store_icon = "✅" if "❌" not in store_name else "❌"
            output.append(f"  {store_icon} 店铺名称: {store_name}")
            
            # 2. 活动信息
            activity_info = scenario.get("活动信息", {})
            output.append("✦ 活动信息:")
            activity_name = activity_info.get("活动名称", "")
            output.append(f"  ✅ 活动名称: {activity_name}")
            
            activity_time = activity_info.get("活动时间", "")
            time_icon = "✅" if "⚠️" not in activity_time else "⚠️"
            output.append(f"  {time_icon} 活动时间: {activity_time}")
            
            # 3. 产品信息
            product_info = scenario.get("产品信息", {})
            output.append("✦ 产品信息:")
            products = product_info.get("主要产品", [])
            product_icon = "✅" if not any("❌" in p for p in products) else "❌"
            output.append(f"  {product_icon} 主要产品: {', '.join(products)}")
            
            features = product_info.get("产品特点", [])
            output.append(f"  ✅ 产品特点: {', '.join(features)}")
            
            # 4. 利益点信息
            benefit_info = scenario.get("利益点信息", {})
            output.append("✦ 利益点信息:")
            
            core_benefits = benefit_info.get("核心权益", [])
            benefit_icon = "✅" if not any("❌" in b for b in core_benefits) else "❌"
            output.append(f"  {benefit_icon} 核心权益: {', '.join(core_benefits)}")
            
            prices = benefit_info.get("价格优势", [])
            output.append(f"  ✅ 价格优势: {', '.join(prices)}")
            
            gifts = benefit_info.get("赠品", [])
            output.append(f"  ✅ 赠品: {', '.join(gifts)}")
            
            # 5. 场景类型
            scenario_type = scenario.get("场景类型", {})
            output.append("✦ 场景类型:")
            output.append(f"  ✅ 优惠券场景: {scenario_type.get('优惠券场景', '')}")
            output.append(f"  ✅ 行业类型: {scenario_type.get('行业类型', '')}")
            if scenario_type.get('宠物类型'):
                output.append(f"  ✅ 宠物类型: {scenario_type.get('宠物类型', '')}")
            
            # 6. 缺失信息
            missing = scenario.get("缺失信息", [])
            if missing:
                output.append("")
                output.append("⚠️  缺失信息:")
                for m in missing:
                    output.append(f"   - {m}")
            
            output.append("")
        
        output.append("=" * 80)
        output.append("请选择下一步操作:")
        output.append("")
        output.append("1️⃣  补充缺失信息（推荐）")
        output.append("    请直接补充上述缺失的信息，我将重新提取确认")
        output.append("")
        output.append("2️⃣  确认生成话术")
        output.append("    如果信息无误或您坚持在缺少信息的情况下生成，请回复'确认生成'")
        output.append("    ⚠️  注意：缺少关键信息可能导致话术质量下降")
        output.append("")
        output.append("3️⃣  重新提供活动信息")
        output.append("    如果提取结果严重错误，请重新提供完整的活动信息")
        output.append("=" * 80)
        
        return "\n".join(output)

def main():
    """测试活动信息提取"""
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
    
    # 输出JSON格式（用于程序调用）
    print("\n\n" + "=" * 80)
    print("JSON格式提取结果（用于程序调用）:")
    print("=" * 80)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()