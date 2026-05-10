#!/usr/bin/env python3
"""修正科技树所有节点的前置条件。

对每个节点从三大类（理论、工程、组织/社会）审查前置条件完整性。
从前沿技术往回逐层追溯，确保无遗漏。
"""

from __future__ import annotations

import json
from pathlib import Path

DATA_PATH = Path("public/data/full_data.json")


def load_data() -> list[dict]:
    """加载原始数据。"""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data: list[dict]) -> None:
    """保存修正后的数据。"""
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_index(data: list[dict]) -> dict[str, dict]:
    """构建节点ID到节点的索引。"""
    return {node["id"]: node for node in data}


def validate_no_cycles(data: list[dict]) -> bool:
    """验证无循环依赖，返回True表示无循环。"""
    index = build_index(data)

    # 拓扑排序检测环
    visited: set[str] = set()
    in_stack: set[str] = set()

    def dfs(node_id: str) -> bool:
        if node_id in in_stack:
            return False  # 发现环
        if node_id in visited:
            return True
        in_stack.add(node_id)
        node = index[node_id]
        for p in node.get("prerequisites", []):
            if p in index:
                if not dfs(p):
                    return False
        in_stack.remove(node_id)
        visited.add(node_id)
        return True

    for node in data:
        if node["id"] not in visited:
            if not dfs(node["id"]):
                return False
    return True


def validate_refs(data: list[dict]) -> list[str]:
    """验证所有前置引用的节点ID存在，返回错误列表。"""
    all_ids = {node["id"] for node in data}
    errors = []
    for node in data:
        for p in node["prerequisites"]:
            if p not in all_ids:
                errors.append(f"{node['id']} -> {p}")
    return errors


def fix_prerequisites(data: list[dict]) -> list[dict]:
    """修正所有节点的前置条件。"""
    index = build_index(data)

    # 定义完整的修正映射
    # 键为节点ID，值为完整的前置条件列表
    corrections: dict[str, list[str]] = {
        # ========================
        # 基础节点 (无前置条件)
        # ========================
        "mat_stone_tools": [],
        "energy_fire": [],
        "math_counting": [],
        "soc_language": [],
        "energy_human_animal": [],
        "phys_magnetism_ancient": [],
        "phys_static_elec": [],

        # ========================
        # 史前时期
        # ========================
        "mat_fire": ["mat_stone_tools"],
        "mat_pottery": ["mat_fire", "mat_stone_tools"],
        "mat_weaving": ["mat_stone_tools"],
        "math_geometry_basic": ["math_counting"],
        "math_arithmetic": ["math_counting"],

        # 农业
        "ag_plant_domestication": ["mat_stone_tools", "soc_language"],
        "ag_animal_domestication": ["mat_stone_tools", "soc_language"],
        "ag_wheat_breeding": ["ag_plant_domestication"],
        "ag_irrigation": ["ag_plant_domestication", "mat_stone_tools"],
        "ag_fermentation": ["ag_plant_domestication", "mat_pottery"],
        "ag_system_rice": ["ag_plant_domestication", "ag_irrigation"],
        "ag_corn_system": ["ag_plant_domestication"],
        "ag_dairy": ["ag_animal_domestication", "ag_fermentation"],
        "ag_plow": ["ag_plant_domestication", "mat_stone_tools", "eng_mechanical"],
        "ag_cattle_breeding": ["ag_animal_domestication"],
        "ag_fertilizer_natural": ["ag_animal_domestication"],
        "ag_silk": ["ag_animal_domestication", "mat_weaving"],
        "ag_food_preserve": ["ag_plant_domestication", "mat_fire"],
        "ag_spice_trade": ["ag_plant_domestication", "soc_trade_route"],
        "ag_crop_rotation": ["ag_plant_domestication", "ag_irrigation"],
        "ag_tea": ["ag_plant_domestication", "ag_fermentation"],
        "ag_terracing": ["ag_irrigation", "ag_plant_domestication", "mat_stone_tools"],
        "ag_sugar": ["ag_plant_domestication", "ag_fermentation"],
        "ag_windmill": ["ag_plant_domestication", "eng_mechanical", "eng_windmill_power"],
        "ag_three_field": ["ag_crop_rotation", "ag_plow"],
        "ag_horse_collar": ["ag_animal_domestication", "ag_plow"],
        "ag_columbian_exchange": ["ag_plant_domestication", "soc_trade_route"],
        "ag_seed_drill": ["ag_plant_domestication", "eng_mechanical", "mat_wrought_iron"],
        "ag_thresher": ["ag_seed_drill", "mat_wrought_iron", "eng_mechanical"],
        "ag_canning": ["ag_food_preserve", "mat_glass", "mat_wrought_iron"],
        "ag_combine": ["ag_thresher", "mat_steel_bessemer", "eng_internal_combustion"],
        "ag_soil_science": ["ag_crop_rotation", "chem_elements"],
        "ag_agronomy": ["ag_soil_science", "chem_organic"],
        "ag_pastuerize": ["ag_canning", "bio_germ_theory"],
        "ag_refrigeration": ["eng_refrigeration", "ag_food_preserve"],
        "ag_biocontrol": ["ag_pesticide", "bio_evolution"],
        "ag_tractor": ["eng_internal_combustion", "ag_plow", "mat_steel_bessemer"],
        "ag_fertilizer_synthetic": ["chem_haber", "ag_fertilizer_natural"],
        "ag_hydroponics": ["ag_fertilizer_synthetic", "ag_irrigation"],
        "ag_pesticide": ["ag_fertilizer_synthetic", "chem_organic"],
        "ag_organic_farming": ["ag_fertilizer_natural", "ag_pesticide"],
        "ag_farm_animal": ["ag_tractor", "ag_fertilizer_synthetic"],
        "ag_green_revolution": ["ag_fertilizer_synthetic", "ag_pesticide", "ag_irrigation"],
        "ag_drip_irrigation": ["ag_irrigation", "eng_plastic_pipe"],
        "ag_aquaculture": ["ag_fertilizer_synthetic", "ag_irrigation"],
        "ag_precision_farming": ["ag_tractor", "eng_gps", "it_computer"],
        "ag_gm_crop": ["bio_genetic_eng", "ag_green_revolution"],
        "ag_vertical_farm": ["ag_hydroponics", "eng_led_light", "energy_electricity_gen"],
        "ag_crispr_crop": ["ag_gm_crop", "bio_crispr"],
        "ag_drone_farming": ["ag_precision_farming", "eng_drone"],

        # 医学（早期）
        "med_trepanation": ["mat_stone_tools"],
        "med_herbal": ["ag_plant_domestication"],

        # 天文
        "astro_ancient_obs": ["math_counting", "soc_writing"],

        # 能源
        "energy_biogas": ["ag_fermentation", "mat_pottery"],

        # 工程（早期）
        "eng_mechanical": ["mat_stone_tools"],
        "eng_wheel": ["mat_stone_tools", "eng_mechanical"],

        # 数学（早期）
        "math_babylonian": ["math_arithmetic", "math_geometry_basic"],
        "math_pythagorean": ["math_geometry_basic", "math_arithmetic"],
        "math_irrational": ["math_pythagorean"],
        "math_axiom": ["math_pythagorean", "math_logic_ancient"],

        # 社会（早期）
        "soc_state": ["soc_language", "ag_plant_domestication"],
        "soc_writing": ["soc_language", "math_counting"],

        # ========================
        # 古代时期
        # ========================
        # 材料
        "mat_copper": ["mat_fire", "mat_stone_tools"],
        "mat_bronze": ["mat_copper", "mat_fire"],
        "mat_glass": ["mat_fire", "mat_pottery"],
        "mat_iron_smelting": ["mat_bronze", "mat_fire"],
        "mat_cast_iron": ["mat_iron_smelting"],
        "mat_steel_ancient": ["mat_iron_smelting", "mat_fire"],
        "mat_cement_roman": ["mat_fire", "mat_stone_tools", "math_geometry_basic"],

        # 化学
        "chem_alchemy_china": ["mat_fire", "mat_pottery"],
        "chem_alchemy_west": ["mat_fire", "mat_bronze", "soc_trade_route"],
        "chem_distillation": ["chem_alchemy_west", "mat_glass"],

        # 物理
        "phys_optics_ancient": ["math_geometry_basic", "mat_glass"],
        "phys_lever": ["math_geometry_basic", "eng_mechanical"],
        "phys_buoyancy": ["math_geometry_basic"],

        # 天文
        "astro_star_catalog": ["astro_ancient_obs", "math_geometry_basic"],

        # 工程
        "eng_architecture_ancient": ["mat_stone_tools", "math_geometry_basic", "eng_mechanical"],
        "eng_water_wheel": ["eng_wheel", "eng_mechanical"],
        "eng_aqueduct": ["eng_mechanical", "math_geometry_basic", "mat_stone_tools"],
        "eng_canal": ["eng_water_wheel", "eng_aqueduct", "mat_stone_tools"],
        "eng_compass": ["phys_magnetism_ancient"],
        "eng_sailing": ["eng_wheel", "mat_weaving"],

        # 社会
        "soc_trade_route": ["soc_state", "soc_money"],
        "soc_law_code": ["soc_writing", "soc_state"],
        "soc_religion_org": ["soc_state", "soc_language"],
        "soc_money": ["soc_state", "mat_copper"],
        "soc_philosophy": ["soc_language", "soc_state"],
        "soc_democracy_ancient": ["soc_state", "soc_law_code"],
        "soc_empire": ["soc_state", "soc_law_code", "mat_bronze"],
        "soc_cultural_exchange": ["soc_writing", "soc_trade_route"],

        # 数学
        "math_conic": ["math_axiom", "math_geometry_basic"],
        "math_trigonometry": ["math_geometry_basic", "math_babylonian"],
        "math_hindu_decimal": ["math_arithmetic", "soc_cultural_exchange"],
        "math_algebra_khwarizmi": ["math_arithmetic", "math_hindu_decimal"],
        "math_fibonacci": ["math_hindu_decimal", "math_algebra_khwarizmi"],

        # 生物
        "bio_natural_history": ["math_counting", "soc_language"],
        "bio_anatomy_ancient": ["bio_natural_history"],
        "botany_dioscorides": ["bio_natural_history", "med_herbal"],

        # 医学
        "med_hippocrates": ["med_herbal", "bio_natural_history"],
        "med_traditional_chinese": ["med_herbal", "soc_philosophy"],
        "med_anatomy_galen": ["bio_anatomy_ancient", "med_hippocrates"],
        "med_hospital": ["med_hippocrates", "soc_religion_org"],
        "med_islamic_medicine": ["med_hippocrates", "med_hospital"],

        # ========================
        # 中世纪/文艺复兴
        # ========================
        # 材料
        "mat_paper": ["mat_weaving", "mat_pottery"],
        "mat_porcelain": ["mat_pottery", "mat_fire"],
        "mat_gunpowder": ["mat_fire", "chem_alchemy_china"],
        "mat_printing_types": ["mat_paper", "eng_mechanical"],
        "mat_pig_iron": ["mat_cast_iron", "mat_fire"],
        "mat_wood_working": ["mat_stone_tools"],

        # 工程
        "eng_gothic": ["eng_architecture_ancient", "mat_stone_tools", "math_geometry_basic"],
        "eng_windmill_power": ["eng_water_wheel", "eng_mechanical"],
        "eng_clock_mech": ["eng_mechanical", "math_arithmetic"],
        "eng_printing_press": ["mat_printing_types", "eng_mechanical"],
        "energy_water_power": ["eng_water_wheel"],
        "energy_wind_power": ["eng_windmill_power"],

        # 天文
        "astro_heliocentric": ["astro_ancient_obs", "math_trigonometry"],
        "astro_telescope_refract": ["mat_glass", "phys_optics_ancient"],
        "astro_planetary_motion": ["astro_heliocentric", "math_trigonometry"],
        "astro_telescope_reflect": ["astro_telescope_refract", "mat_glass", "phys_optics_ancient"],

        # 物理
        "phys_heliocentric": ["math_trigonometry", "phys_optics_ancient"],
        "phys_telescope": ["phys_optics_ancient", "mat_glass"],

        # 化学
        "chem_elements": ["chem_alchemy_west", "math_axiom"],

        # 社会
        "soc_feudalism": ["soc_empire", "soc_religion_org"],
        "soc_university": ["soc_philosophy", "soc_religion_org"],
        "soc_magna_carta": ["soc_feudalism", "soc_law_code"],
        "soc_renaissance": ["soc_university", "soc_philosophy", "soc_cultural_exchange"],
        "soc_reformation": ["soc_renaissance", "eng_printing_press"],
        "soc_nation_state": ["soc_magna_carta", "soc_reformation"],

        # ========================
        # 科学革命/工业革命
        # ========================
        # 数学
        "math_logarithm": ["math_trigonometry", "math_hindu_decimal"],
        "math_analytic_geometry": ["math_axiom", "math_algebra_khwarizmi"],
        "math_probability": ["math_arithmetic", "math_counting"],
        "math_calculus": ["math_analytic_geometry", "math_logarithm"],
        "math_graph_theory": ["math_axiom"],
        "math_euler_formula": ["math_calculus", "math_trigonometry"],
        "math_bayesian": ["math_probability", "math_calculus"],

        # 物理
        "phys_kinematics": ["math_calculus", "math_geometry_basic"],
        "phys_kepler": ["math_trigonometry", "phys_heliocentric"],
        "phys_gravity": ["phys_kinematics", "math_calculus", "phys_kepler"],
        "phys_classical_mechanics": ["phys_gravity", "math_calculus"],
        "phys_electromagnetism": ["phys_static_elec", "phys_magnetism_ancient", "math_calculus"],
        "phys_vector_calculus": ["math_calculus", "math_analytic_geometry"],
        "phys_thermodynamics_1": ["phys_classical_mechanics", "math_calculus"],
        "phys_thermodynamics_2": ["phys_thermodynamics_1"],
        "phys_maxwell": ["phys_electromagnetism", "math_calculus", "phys_vector_calculus"],
        "phys_spectrum": ["phys_optics_ancient", "phys_maxwell"],

        # 化学
        "chem_gas_laws": ["math_calculus", "chem_elements"],
        "chem_phlogiston": ["chem_elements"],
        "chem_oxygen": ["chem_phlogiston", "chem_elements"],
        "chem_electrolysis": ["phys_electromagnetism", "chem_elements"],
        "chem_electrochemistry": ["phys_electromagnetism", "chem_elements"],
        "chem_atomic_theory": ["chem_oxygen", "chem_elements"],
        "chem_organic": ["chem_atomic_theory", "chem_oxygen"],
        "chem_catalysis": ["chem_atomic_theory", "chem_organic"],
        "chem_thermochem": ["phys_thermodynamics_1", "chem_elements"],
        "chem_nitrocellulose": ["chem_organic", "chem_elements"],
        "chem_kinetics": ["chem_thermochem", "math_calculus"],
        "chem_synthetic_dye": ["chem_organic", "chem_structural"],
        "chem_structural": ["chem_organic", "chem_atomic_theory"],
        "chem_periodic": ["chem_atomic_theory", "math_matrix"],
        "chem_stereo": ["chem_structural"],
        "chem_ionic_theory": ["chem_electrolysis"],
        "chem_acid_base": ["chem_electrolysis", "chem_ionic_theory"],

        # 生物
        "bio_microscope": ["mat_glass", "phys_optics_ancient"],
        "bio_taxonomy": ["bio_natural_history", "math_logic"],
        "bio_evolution": ["bio_taxonomy", "bio_natural_history", "math_probability"],
        "bio_cell_theory": ["bio_microscope", "bio_taxonomy"],
        "bio_embryology": ["bio_microscope", "bio_cell_theory"],
        "bio_germ_theory": ["bio_microscope", "bio_cell_theory"],
        "bio_genetics_mendel": ["bio_evolution", "math_probability"],
        "bio_ecology": ["bio_evolution", "bio_taxonomy"],

        # 天文
        "astro_gravity_apply": ["astro_planetary_motion", "phys_gravity"],
        "astro_comet_predict": ["astro_gravity_apply", "math_calculus"],
        "astro_planet_formation": ["astro_heliocentric", "phys_gravity"],
        "astro_uranus_discovery": ["astro_telescope_reflect"],
        "astro_celestial_mechanics": ["astro_gravity_apply", "math_calculus"],
        "astro_stellar_parallax": ["astro_telescope_reflect", "math_trigonometry"],
        "astro_photography": ["astro_telescope_reflect", "eng_photography"],
        "astro_neptune_predict": ["astro_celestial_mechanics", "astro_uranus_discovery"],
        "astro_spectroscopy": ["phys_spectrum", "astro_telescope_reflect"],

        # 能源
        "energy_coal": ["mat_fire", "eng_mining"],
        "energy_steam_power": ["eng_steam_engine", "energy_coal"],
        "energy_battery_voltaic": ["phys_electromagnetism", "chem_electrochemistry"],
        "energy_electricity_gen": ["eng_generator", "energy_coal"],
        "energy_photovoltaic_effect": ["phys_electromagnetism"],
        "energy_heat_pump": ["phys_thermodynamics_2", "eng_refrigeration"],
        "energy_oil": ["eng_internal_combustion", "chem_organic", "eng_drilling"],
        "energy_rechargeable": ["energy_battery_voltaic", "chem_electrochemistry"],
        "energy_pipeline": ["mat_cast_iron", "energy_oil"],
        "energy_hydroelectric": ["eng_generator", "energy_water_power"],
        "energy_ac_power": ["eng_power_grid", "phys_maxwell"],
        "energy_diesel_gen": ["eng_diesel", "eng_generator"],

        # 工程
        "eng_steam_atmospheric": ["mat_blast_furnace_modern", "phys_thermodynamics_1"],
        "eng_fluid_mechanics": ["math_calculus", "phys_classical_mechanics"],
        "eng_steam_engine": ["eng_steam_atmospheric", "mat_wrought_iron"],
        "eng_railway": ["eng_steam_engine", "mat_steel_bessemer", "eng_wheel"],
        "eng_steamship": ["eng_steam_engine", "eng_fluid_mechanics"],
        "eng_electromagnet": ["phys_electromagnetism"],
        "eng_generator": ["phys_electromagnetism", "eng_mechanical"],
        "eng_electric_motor": ["phys_electromagnetism", "eng_mechanical"],
        "eng_telegraph": ["phys_electromagnetism", "eng_electric_motor"],
        "eng_plumbing": ["mat_cast_iron", "eng_water_wheel"],
        "eng_refrigeration": ["phys_thermodynamics_1", "eng_mechanical"],
        "eng_elevator": ["eng_mechanical", "mat_steel_bessemer"],
        "eng_reinforced_concrete": ["mat_cement_roman", "mat_steel_bessemer"],
        "eng_tunnel_boring": ["mat_steel_bessemer", "eng_mechanical"],
        "eng_suspension_bridge": ["mat_steel_bessemer", "math_calculus", "eng_structural_analysis"],
        "eng_structural_analysis": ["math_calculus", "phys_classical_mechanics"],
        "eng_internal_combustion": ["phys_thermodynamics_1", "chem_gas_laws", "eng_mechanical"],
        "eng_power_grid": ["eng_generator", "eng_electric_motor", "phys_maxwell"],
        "eng_skyscraper": ["eng_reinforced_concrete", "eng_elevator", "mat_steel_bessemer"],
        "eng_automobile": ["eng_internal_combustion", "mat_rubber_vulcan", "eng_mechanical"],
        "eng_diesel": ["eng_internal_combustion", "phys_thermodynamics_2"],
        "eng_airplane": ["eng_internal_combustion", "phys_classical_mechanics", "mat_aluminum", "eng_fluid_mechanics"],
        "eng_assembly_line": ["eng_automobile", "mat_steel_bessemer", "soc_industrial_society"],
        "eng_rocket": ["eng_internal_combustion", "phys_classical_mechanics", "eng_fluid_mechanics"],
        "eng_photography": ["mat_glass", "chem_elements"],
        "eng_mining": ["mat_stone_tools", "mat_fire"],
        "eng_drilling": ["eng_mechanical", "mat_steel_bessemer"],

        # 材料
        "mat_blast_furnace_modern": ["mat_pig_iron", "mat_coke"],
        "mat_coke": ["mat_fire", "mat_pig_iron"],
        "mat_wrought_iron": ["mat_blast_furnace_modern"],
        "mat_rubber_vulcan": ["mat_fire", "chem_elements"],
        "mat_steel_bessemer": ["mat_wrought_iron", "mat_blast_furnace_modern"],
        "mat_open_hearth": ["mat_steel_bessemer"],
        "mat_dynamite": ["mat_gunpowder", "chem_nitrocellulose"],
        "mat_aluminum": ["mat_fire", "chem_electrolysis", "energy_electricity_gen"],

        # 社会
        "soc_enlightenment": ["soc_renaissance", "soc_philosophy", "soc_nation_state"],
        "soc_capitalism": ["soc_money", "eng_steam_engine", "soc_enlightenment"],
        "soc_economics": ["math_statistics_modern", "soc_capitalism"],
        "soc_democracy_modern": ["soc_enlightenment", "soc_nation_state"],
        "soc_industrial_society": ["soc_capitalism", "eng_steam_engine"],
        "soc_sociology": ["math_statistics_modern", "soc_philosophy"],
        "soc_socialism": ["soc_industrial_society", "soc_capitalism"],
        "soc_feminism_wave1": ["soc_democracy_modern", "soc_labor_movement"],
        "soc_labor_movement": ["soc_socialism", "soc_industrial_society"],
        "soc_public_education": ["soc_democracy_modern", "soc_industrial_society"],
        "soc_psychology": ["soc_philosophy", "math_statistics_modern"],

        # 医学
        "med_dissection": ["med_anatomy_galen", "soc_renaissance"],
        "med_circulation": ["med_dissection", "phys_classical_mechanics"],
        "med_vaccination": ["med_herbal", "bio_natural_history"],
        "med_anesthesia": ["chem_elements", "eng_mechanical"],
        "med_germ_disease": ["bio_germ_theory", "med_antiseptic"],
        "med_epidemiology": ["math_statistics_modern", "med_germ_disease"],
        "med_public_health": ["med_epidemiology", "med_germ_disease", "soc_democracy_modern"],
        "med_antiseptic": ["bio_germ_theory", "med_anesthesia"],
        "med_xray": ["phys_electron"],
        "med_mental_illness": ["med_hippocrates", "bio_nervous"],
        "med_blood_transfusion": ["med_circulation", "chem_elements"],
        "med_vitamin": ["chem_organic", "med_herbal"],
        "med_insulin": ["med_germ_disease", "bio_cell_theory", "chem_organic"],

        # ========================
        # 现代（20世纪上半叶）
        # ========================
        # 物理
        "phys_radioactivity": ["phys_electron"],
        "phys_electron": ["phys_electromagnetism", "phys_thermodynamics_2"],
        "phys_blackbody": ["phys_thermodynamics_2", "phys_maxwell"],
        "phys_relativity_special": ["phys_maxwell", "math_non_euclidean"],
        "phys_superconductor": ["phys_electron", "phys_thermodynamics_2"],
        "phys_relativity_general": ["phys_relativity_special", "math_relativity_math", "math_tensor"],
        "phys_quantum_theory": ["phys_blackbody", "phys_electron", "math_matrix", "math_group_theory"],
        "phys_uncertainty": ["phys_quantum_theory"],
        "phys_antimatter": ["phys_relativity_special", "phys_quantum_theory"],
        "phys_nuclear_structure": ["phys_radioactivity", "phys_quantum_theory"],
        "phys_dark_matter": ["phys_gravity", "phys_relativity_general"],
        "phys_entanglement": ["phys_quantum_theory", "phys_uncertainty"],
        "phys_nuclear_fission": ["phys_nuclear_structure", "phys_relativity_special"],
        "phys_nuclear_fusion": ["phys_nuclear_structure", "phys_relativity_special"],
        "phys_quantum_field": ["phys_quantum_theory", "phys_relativity_special", "math_group_theory"],
        "phys_laser": ["phys_quantum_theory", "phys_electromagnetism"],
        "phys_standard_model": ["phys_quantum_theory", "phys_nuclear_structure", "math_group_theory"],
        "phys_higgs": ["phys_standard_model", "phys_quantum_theory"],
        "phys_cosmic_background": ["phys_relativity_general", "phys_thermodynamics_2"],
        "phys_string_theory": ["phys_standard_model", "phys_relativity_general", "math_topology"],

        # 数学
        "math_least_squares": ["math_calculus", "math_probability"],
        "math_fourier": ["math_calculus", "math_trigonometry"],
        "math_non_euclidean": ["math_axiom", "math_analytic_geometry"],
        "math_group_theory": ["math_axiom", "math_algebra_khwarizmi"],
        "math_boolean": ["math_axiom"],
        "math_matrix": ["math_algebra_khwarizmi", "math_analytic_geometry"],
        "math_set_theory": ["math_axiom", "math_boolean"],
        "math_logic": ["math_axiom", "math_boolean"],
        "math_topology": ["math_set_theory", "math_analytic_geometry"],
        "math_hilbert": ["math_set_theory", "math_logic"],
        "math_tensor": ["math_matrix", "math_calculus"],
        "math_measure_theory": ["math_set_theory", "math_calculus"],
        "math_relativity_math": ["math_non_euclidean", "math_calculus", "math_tensor"],
        "math_statistics_modern": ["math_probability", "math_least_squares", "math_measure_theory"],
        "math_number_theory": ["math_set_theory", "math_algebra_khwarizmi"],
        "math_incompleteness": ["math_logic", "math_hilbert"],
        "math_turing": ["math_logic", "math_incompleteness"],
        "math_linear_prog": ["math_matrix", "math_algebra_khwarizmi"],
        "math_game_theory": ["math_probability", "math_set_theory"],
        "math_categorical": ["math_set_theory", "math_topology", "math_group_theory"],
        "math_optimization": ["math_calculus", "math_matrix", "math_linear_prog"],
        "math_information_theory": ["math_probability", "math_logarithm"],
        "math_control_theory": ["math_calculus", "math_probability", "math_matrix"],
        "math_complexity_theory": ["math_turing", "math_logic"],
        "math_graph_algorithms": ["math_graph_theory", "math_complexity_theory"],
        "math_chaos_theory": ["math_calculus", "math_topology"],
        "math_fuzzy_logic": ["math_set_theory", "math_logic"],
        "math_fractal": ["math_topology", "math_chaos_theory"],
        "math_rsa": ["math_number_theory", "math_information_theory"],
        "math_randomized_algo": ["math_probability", "math_complexity_theory"],
        "math_wavelet": ["math_fourier", "math_set_theory"],
        "math_homotopy_type": ["math_topology", "math_logic", "math_incompleteness"],

        # 化学
        "chem_radiochemistry": ["phys_radioactivity", "chem_atomic_theory"],
        "chem_chromatography": ["chem_organic", "chem_structural"],
        "chem_photochemistry": ["phys_quantum_theory", "chem_organic"],
        "chem_haber": ["chem_elements", "phys_thermodynamics_1", "chem_catalysis"],
        "chem_crystallography": ["phys_electromagnetism", "math_fourier"],
        "chem_isotope": ["chem_radiochemistry", "phys_electron"],
        "chem_periodic_modern": ["chem_periodic", "phys_electron", "chem_isotope"],
        "chem_bond_theory": ["phys_electron", "chem_structural"],
        "chem_polymer_theory": ["chem_organic", "chem_structural"],
        "chem_petrochem": ["chem_organic", "chem_catalysis", "mat_steel_bessemer", "energy_oil"],
        "chem_quantum_chem": ["phys_quantum_theory", "chem_bond_theory"],
        "chem_mo_theory": ["chem_quantum_chem", "phys_quantum_theory"],
        "chem_covalent_modern": ["chem_quantum_chem", "chem_mo_theory"],
        "chem_nmr": ["phys_quantum_theory", "phys_electromagnetism", "eng_electromagnet"],
        "chem_asymmetric": ["chem_stereo", "chem_catalysis"],
        "chem_cheminformatics": ["it_computer", "chem_organic"],
        "chem_combinatorial": ["chem_organic", "it_computer", "chem_synthetic_dye"],
        "chem_green": ["chem_polymer_theory", "chem_catalysis"],
        "chem_metal_organic": ["chem_organic", "chem_catalysis"],
        "chem_click_chemistry": ["chem_organic", "chem_catalysis"],
        "chem_flow_chem": ["chem_green", "chem_catalysis"],

        # 生物
        "bio_virology": ["bio_germ_theory", "bio_microscope"],
        "bio_chromosome": ["bio_genetics_mendel", "bio_cell_theory"],
        "bio_nervous": ["bio_cell_theory", "bio_anatomy_ancient"],
        "bio_neuroplasticity": ["bio_nervous", "bio_cell_theory"],
        "bio_molecular_bio": ["bio_dna", "bio_genetics_mendel", "chem_organic"],
        "bio_dna": ["bio_chromosome", "chem_crystallography", "phys_quantum_theory"],
        "bio_central_dogma": ["bio_dna"],
        "bio_genetic_code": ["bio_central_dogma", "bio_dna"],
        "bio_mitochondria": ["bio_cell_theory", "bio_evolution"],
        "bio_restriction_enzyme": ["bio_dna", "bio_central_dogma"],
        "bio_signal_transduction": ["bio_molecular_bio", "bio_cell_theory"],
        "bio_circadian": ["bio_genetics_mendel", "bio_molecular_bio"],
        "bio_apoptosis": ["bio_cell_theory", "bio_molecular_bio"],
        "bio_genetic_eng": ["bio_restriction_enzyme", "bio_dna"],
        "bio_epigenetics": ["bio_dna", "bio_central_dogma"],
        "bio_bioinformatics": ["it_computer", "bio_dna", "math_statistics_modern"],
        "bio_gmo": ["bio_genetic_eng", "bio_restriction_enzyme"],
        "bio_pcr": ["bio_dna", "bio_genetic_eng"],
        "bio_protein_struct": ["bio_genome_human", "bio_dna", "bio_molecular_bio"],
        "bio_cloning": ["bio_cell_theory", "bio_genetic_eng"],
        "bio_stem_cell": ["bio_cell_theory", "bio_dna", "bio_embryology"],
        "bio_rna_interference": ["bio_central_dogma", "bio_genetic_eng"],
        "bio_genome_human": ["bio_pcr", "it_computer", "bio_dna", "bio_bioinformatics"],
        "bio_connectome": ["bio_nervous", "bio_bioinformatics"],
        "bio_microbiome": ["bio_genome_human", "bio_germ_theory"],
        "bio_single_cell": ["bio_pcr", "bio_genome_human"],
        "bio_organoid": ["bio_stem_cell", "bio_cell_theory"],
        "bio_crispr": ["bio_genetic_eng", "bio_genome_human", "bio_restriction_enzyme"],
        "bio_synth_bio": ["bio_crispr", "bio_genetic_eng", "bio_genome_human"],
        "bio_xenobiology": ["bio_synth_bio", "bio_genetic_eng"],
        "bio_mrna_vaccine": ["bio_pcr", "bio_central_dogma", "bio_rna_interference"],
        "bio_protein_folding": ["bio_bioinformatics", "it_deep_learning", "bio_protein_struct"],
        "bio_alphafold2": ["bio_protein_folding", "bio_bioinformatics", "it_deep_learning", "it_attention", "chem_crystallography"],

        # 天文
        "astro_cepheid": ["astro_stellar_parallax", "astro_photography"],
        "astro_hertzsprung": ["astro_spectroscopy", "astro_stellar_parallax"],
        "astro_general_relativity_apply": ["phys_relativity_general", "astro_telescope_reflect"],
        "astro_galaxy": ["astro_stellar_parallax", "astro_hertzsprung"],
        "astro_expanding_universe": ["astro_galaxy", "astro_spectroscopy"],
        "astro_radio_astronomy": ["phys_electromagnetism", "phys_maxwell", "it_signal_processing"],
        "astro_dark_matter": ["astro_galaxy", "phys_gravity"],
        "astro_supernova_theory": ["astro_hertzsprung", "phys_nuclear_fusion"],
        "astro_stellar_nucleosynthesis": ["phys_nuclear_fusion", "astro_hertzsprung"],
        "astro_stellar_evolution": ["astro_hertzsprung", "phys_nuclear_fusion", "astro_stellar_nucleosynthesis"],
        "astro_xray": ["phys_electromagnetism", "astro_radio_astronomy"],
        "astro_cmb": ["astro_big_bang", "phys_electromagnetism"],
        "astro_infrared": ["phys_electromagnetism", "phys_maxwell"],
        "astro_pulsar": ["astro_radio_astronomy"],
        "astro_black_hole": ["phys_relativity_general", "astro_xray"],
        "astro_pulsar_timing": ["astro_pulsar"],
        "astro_grav_lens": ["phys_relativity_general", "astro_galaxy"],
        "astro_cosmic_inflation": ["astro_big_bang", "phys_relativity_general"],
        "astro_neutrino_astronomy": ["astro_supernova_theory", "phys_neutrino"],
        "astro_space_telescope": ["astro_telescope_reflect", "eng_rocket", "eng_satellite"],
        "astro_exoplanet": ["astro_spectroscopy", "astro_telescope_reflect"],
        "astro_dark_energy": ["astro_expanding_universe", "astro_cmb"],
        "astro_cmb_satellite": ["astro_cmb", "astro_space_telescope"],
        "astro_planet_migration": ["astro_exoplanet", "astro_planet_formation"],
        "astro_big_bang": ["astro_expanding_universe", "phys_relativity_general"],
        "astro_gravitational_wave": ["phys_relativity_general", "phys_laser", "it_signal_processing"],
        "astro_multi_messenger": ["astro_gravitational_wave", "astro_neutrino_astronomy"],
        "astro_jwst": ["astro_space_telescope", "astro_infrared", "eng_rocket"],

        # 能源
        "energy_geothermal": ["energy_electricity_gen", "eng_drilling"],
        "energy_pumped_storage": ["energy_hydroelectric", "eng_generator"],
        "energy_plasma": ["phys_quantum_theory", "phys_electromagnetism"],
        "energy_hydro_electric_dam": ["energy_hydroelectric", "eng_reinforced_concrete"],
        "energy_gas_turbine": ["eng_jet_engine", "phys_thermodynamics_2"],
        "energy_nuclear": ["eng_nuclear_reactor", "phys_nuclear_fission"],
        "energy_solar_cell": ["energy_photovoltaic_effect", "mat_silicon_purify"],
        "energy_hydrogen_fuel": ["phys_electromagnetism", "chem_electrochemistry"],
        "energy_tidal": ["energy_hydroelectric", "phys_gravity"],
        "energy_efficiency": ["energy_nuclear", "energy_oil"],
        "energy_wind_turbine": ["energy_wind_power", "eng_generator", "mat_fiber_glass"],
        "energy_concentrated_solar": ["energy_solar_cell", "eng_mechanical"],
        "energy_lithium_ion": ["energy_rechargeable", "chem_electrochemistry", "mat_nanomaterial"],
        "energy_carbon_capture": ["chem_gas_laws", "energy_coal"],
        "energy_wave": ["energy_tidal", "phys_classical_mechanics"],
        "energy_smart_grid": ["energy_ac_power", "it_computer", "it_internet"],
        "energy_energy_mgmt": ["energy_smart_grid", "it_cloud"],
        "energy_grid_storage": ["energy_lithium_ion", "energy_smart_grid"],
        "energy_solid_state": ["energy_lithium_ion", "mat_nanomaterial", "chem_electrolysis"],
        "energy_microreactor": ["energy_nuclear", "eng_control_system"],
        "energy_green_hydrogen": ["energy_hydrogen_fuel", "energy_solar_cell", "chem_electrolysis"],
        "energy_nuclear_fusion_reactor": [
            "phys_nuclear_fusion", "energy_plasma", "eng_nuclear_reactor",
            "eng_superconductor_magnet", "eng_high_temp_material"
        ],

        # 工程
        "eng_jet_engine": ["eng_internal_combustion", "mat_superalloy", "eng_fluid_mechanics"],
        "eng_nuclear_reactor": ["phys_nuclear_fission", "eng_plumbing", "eng_control_system"],
        "eng_control_system": ["math_control_theory", "eng_mechanical", "it_computer"],
        "eng_plastic_pipe": ["mat_polyethylene", "eng_mechanical"],
        "eng_cnc": ["it_computer", "eng_mechanical", "eng_control_system"],
        "eng_avionics": ["it_computer", "eng_control_system", "eng_airplane"],
        "eng_satellite": ["eng_rocket", "phys_relativity_special", "it_computer", "eng_control_system"],
        "eng_vtol": ["eng_airplane", "eng_internal_combustion", "eng_control_system"],
        "eng_spacecraft": ["eng_satellite", "eng_rocket", "mat_titanium", "eng_avionics"],
        "eng_robotics": ["it_computer", "eng_mechanical", "math_control_theory", "eng_electric_motor"],
        "eng_led_light": ["phys_quantum_theory", "mat_silicon_purify"],
        "eng_superconductor_magnet": ["phys_superconductor", "eng_electromagnet", "mat_superconductor"],
        "eng_gps": ["eng_satellite", "phys_relativity_special", "it_computer"],
        "eng_microelectromech": ["mat_lithography", "eng_cnc"],
        "eng_drone": ["eng_airplane", "eng_avionics", "eng_robotics", "eng_gps", "it_wireless"],
        "eng_ev": ["eng_automobile", "energy_lithium_ion", "eng_electric_motor"],
        "eng_reusable_rocket": [
            "eng_rocket", "eng_avionics", "eng_vtol", "eng_control_system",
            "eng_gps", "mat_carbon_fiber"
        ],
        "eng_high_temp_material": ["mat_superalloy", "mat_titanium"],

        # IT
        "it_abacus": ["math_counting"],
        "it_mechanical_calc": ["math_arithmetic", "eng_mechanical"],
        "it_punch_card": ["it_mechanical_calc", "mat_paper"],
        "it_analytical_engine": ["it_mechanical_calc", "it_punch_card"],
        "it_wireless": ["phys_maxwell", "eng_electric_motor"],
        "it_boolean_logic": ["math_boolean", "math_turing"],
        "it_colossus": ["it_boolean_logic", "math_turing", "eng_electromagnet"],
        "it_neural_network": ["math_boolean", "math_calculus", "math_probability"],
        "it_eniac": ["it_colossus", "phys_electron", "eng_electromagnet"],
        "it_stored_program": ["it_eniac", "math_turing"],
        "it_transistor": ["phys_quantum_theory", "mat_silicon_purify"],
        "it_signal_processing": ["math_fourier", "math_information_theory"],
        "it_nlp": ["math_logic", "it_computer"],
        "it_computer": ["it_transistor", "it_stored_program"],
        "it_high_level_lang": ["it_stored_program", "math_logic"],
        "it_integrated_circuit": ["it_transistor", "mat_lithography"],
        "it_operating_system": ["it_computer", "it_high_level_lang"],
        "it_digital": ["math_fourier", "it_computer"],
        "it_software_eng": ["it_high_level_lang", "it_operating_system"],
        "it_relational_db": ["it_computer", "math_set_theory"],
        "it_microprocessor": ["it_integrated_circuit", "mat_lithography"],
        "it_email": ["it_internet"],
        "it_vlsi": ["it_integrated_circuit", "mat_lithography"],
        "it_tcp_ip": ["it_computer", "math_information_theory"],
        "it_fiber_optic": ["mat_optical_fiber", "phys_laser"],
        "it_cryptography": ["math_rsa", "it_computer"],
        "it_personal_computer": ["it_microprocessor", "it_operating_system"],
        "it_mobile_network": ["it_wireless", "it_digital"],
        "it_internet": ["it_tcp_ip", "eng_power_grid"],
        "it_graphical_ui": ["it_personal_computer"],
        "it_parallel_computing": ["it_vlsi", "it_server_farm"],
        "it_backprop": ["it_neural_network", "math_calculus"],
        "it_world_wide_web": ["it_internet", "math_information_theory"],
        "it_open_source": ["it_operating_system", "it_internet"],
        "it_battery": ["energy_lithium_ion"],
        "it_server_farm": ["it_computer", "it_internet", "eng_power_grid"],
        "it_search_engine": ["it_world_wide_web", "math_probability"],
        "it_reinforcement": ["math_probability", "math_calculus", "it_neural_network"],
        "it_social_media": ["it_world_wide_web", "it_smartphone"],
        "it_cloud": ["it_internet", "it_server_farm"],
        "it_big_data": ["it_cloud", "it_digital"],
        "it_smartphone": ["it_personal_computer", "it_wireless", "mat_lcd", "it_mobile_network"],
        "it_gpu": ["it_integrated_circuit", "it_neural_network"],
        "it_blockchain": ["it_cryptography", "math_game_theory"],
        "it_devops": ["it_cloud", "it_open_source"],
        "it_deep_learning": ["it_neural_network", "it_gpu", "math_calculus", "it_backprop"],
        "it_computer_vision": ["it_deep_learning", "it_neural_network"],
        "it_attention": ["it_neural_network", "math_probability"],
        "it_chip_interconnect": ["it_gpu", "it_vlsi"],
        "it_framework_dl": ["it_gpu", "it_neural_network", "it_open_source"],
        "it_advanced_process": ["it_integrated_circuit", "mat_lithography", "mat_nanomaterial", "phys_quantum_theory"],
        "it_model_distillation": ["it_deep_learning", "it_neural_network"],
        "it_transformer": ["it_deep_learning", "it_attention"],
        "it_compute_cluster": ["it_cloud", "it_gpu", "it_chip_interconnect"],
        "it_model_quantization": ["it_deep_learning", "it_gpu"],
        "it_pretraining": ["it_transformer", "it_gpu"],
        "it_vector_db": ["it_llm", "it_relational_db"],
        "it_distributed_training": ["it_compute_cluster", "it_framework_dl"],
        "it_llm": ["it_transformer", "it_pretraining", "it_compute_cluster", "it_distributed_training"],
        "it_dalle": ["it_transformer", "it_pretraining", "it_deep_learning"],
        "it_rlhf": ["it_llm", "it_reinforcement", "math_game_theory"],
        "it_diffusion": ["it_deep_learning", "it_attention", "it_compute_cluster"],
        "it_chatgpt": ["it_llm", "it_rlhf"],
        "it_gpt4": ["it_chatgpt", "it_rlhf", "it_compute_cluster", "it_advanced_process"],
        "it_llama": ["it_llm", "it_pretraining"],
        "it_multimodal": ["it_llm", "it_computer_vision", "it_transformer"],
        "it_rag": ["it_llm", "it_vector_db"],
        "it_ai_agent": ["it_gpt4", "it_rag", "it_reinforcement"],
        "it_sora": ["it_diffusion", "it_transformer", "it_compute_cluster"],
        "it_reasoning": ["it_gpt4", "it_rlhf", "it_reinforcement"],
        "it_code_gen": ["it_gpt4", "it_llm"],
        "it_deepseek": ["it_reasoning", "it_llama", "it_model_distillation", "it_model_quantization"],
        "it_agentic": ["it_ai_agent", "it_reasoning"],
        "it_deep_research": ["it_ai_agent", "it_rag", "it_reasoning"],
        "it_mcp": ["it_ai_agent"],

        # 材料
        "mat_alloy_steel": ["mat_steel_bessemer"],
        "mat_bakelite": ["chem_synthetic_dye", "mat_fire", "chem_polymer_theory"],
        "mat_stainless_steel": ["mat_steel_bessemer", "mat_open_hearth"],
        "mat_polyethylene": ["mat_bakelite", "chem_polymer_theory"],
        "mat_nylon": ["mat_bakelite", "chem_polymer_theory"],
        "mat_fiber_glass": ["mat_glass", "mat_weaving"],
        "mat_superalloy": ["mat_alloy_steel", "mat_stainless_steel"],
        "mat_titanium": ["mat_aluminum", "chem_electrolysis"],
        "mat_silicon_purify": ["mat_aluminum", "chem_electrolysis"],
        "mat_lithography": ["mat_glass", "mat_silicon_purify", "phys_quantum_theory"],
        "mat_cvd": ["mat_silicon_purify", "chem_organic"],
        "mat_biomaterial": ["mat_stainless_steel", "mat_polyethylene"],
        "mat_shape_memory": ["mat_titanium", "mat_alloy_steel"],
        "mat_kevlar": ["mat_nylon", "chem_polymer_theory"],
        "mat_rare_earth": ["mat_alloy_steel", "chem_periodic"],
        "mat_lcd": ["mat_silicon_purify", "chem_organic"],
        "mat_carbon_fiber": ["mat_fiber_glass", "mat_silicon_purify"],
        "mat_optical_fiber": ["mat_fiber_glass", "mat_silicon_purify", "phys_laser"],
        "mat_nanomaterial": ["mat_silicon_purify", "phys_quantum_theory"],
        "mat_superconductor": ["mat_silicon_purify", "phys_superconductor"],
        "mat_3d_print": ["mat_nanomaterial", "mat_polyethylene", "it_computer"],
        "mat_quantum_dot": ["mat_nanomaterial", "phys_quantum_theory"],
        "mat_metamaterial": ["mat_nanomaterial", "mat_lithography"],
        "mat_graphene": ["mat_nanomaterial", "mat_carbon_fiber"],
        "mat_perovskite": ["mat_nanomaterial", "mat_silicon_purify"],

        # 物理（现代）
        "phys_quantum_computing": ["phys_entanglement", "math_turing", "math_information_theory"],
        "phys_quantum_teleport": ["phys_entanglement", "math_information_theory"],
        "phys_dark_energy": ["phys_relativity_general", "phys_cosmic_background"],
        "phys_neutrino": ["phys_nuclear_structure", "phys_quantum_theory"],
        "phys_topological_insulator": ["phys_quantum_theory", "math_topology", "mat_nanomaterial"],
        "phys_gravitational_wave": ["phys_relativity_general", "phys_laser", "it_signal_processing"],

        # 医学（现代）
        "med_antibiotics": ["bio_germ_theory", "med_antiseptic"],
        "med_chemotherapy": ["med_antibiotics", "chem_organic"],
        "med_organ_transplant": ["med_antiseptic", "med_blood_transfusion", "bio_cell_theory"],
        "med_polio_vaccine": ["med_vaccination", "bio_cell_theory"],
        "med_pill": ["med_chemotherapy", "chem_organic"],
        "med_ct_scan": ["med_xray", "it_computer", "math_fourier"],
        "med_mri": ["chem_nmr", "it_computer", "phys_quantum_theory"],
        "med_stent": ["mat_stainless_steel", "med_xray"],
        "med_minimally_invasive": ["med_anesthesia", "med_ct_scan", "it_fiber_optic"],
        "med_gene_therapy": ["bio_genetic_eng", "bio_dna"],
        "med_antiretroviral": ["bio_virology", "med_chemotherapy"],
        "med_stroke_treatment": ["med_ct_scan", "med_blood_transfusion"],
        "med_targeted_therapy": ["med_chemotherapy", "bio_molecular_bio", "bio_genome_human"],
        "med_tissue_eng": ["bio_stem_cell", "mat_biomaterial"],
        "med_robotic_surgery": ["med_minimally_invasive", "eng_robotics"],
        "med_nanomedicine": ["mat_nanomaterial", "med_targeted_therapy"],
        "med_telemedicine": ["it_internet", "it_smartphone"],
        "med_immunotherapy": ["bio_immunology", "med_targeted_therapy"],
        "med_precision": ["bio_genome_human", "med_targeted_therapy", "it_big_data"],
        "med_ai_diagnosis": ["it_deep_learning", "med_mri", "it_big_data"],
        "med_3d_print_organ": ["mat_3d_print", "med_tissue_eng", "bio_stem_cell"],
        "med_crispr_therapy": ["bio_crispr", "med_gene_therapy"],

        # 生物
        "bio_immunology": ["bio_germ_theory", "bio_cell_theory"],
        "bio_paleontology": ["bio_natural_history", "math_counting"],

        # 社会（现代）
        "soc_mass_media": ["eng_telegraph", "eng_steam_engine", "eng_printing_press"],
        "soc_welfare_state": ["soc_socialism", "soc_democracy_modern"],
        "soc_cold_war": ["soc_socialism", "soc_capitalism", "phys_nuclear_fission"],
        "soc_human_rights": ["soc_democracy_modern", "soc_enlightenment"],
        "soc_global_governance": ["soc_human_rights", "soc_cold_war"],
        "soc_decolonization": ["soc_human_rights", "soc_nation_state"],
        "soc_consumer_society": ["soc_capitalism", "eng_assembly_line", "soc_industrial_society"],
        "soc_civil_rights": ["soc_human_rights", "soc_feminism_wave1"],
        "soc_cognitive_science": ["math_logic", "bio_nervous", "soc_psychology", "it_computer"],
        "soc_population_transition": ["med_public_health", "soc_welfare_state"],
        "soc_feminism_wave2": ["soc_feminism_wave1", "soc_civil_rights"],
        "soc_environmentalism": ["soc_consumer_society", "bio_ecology"],
        "soc_behavioral_econ": ["soc_economics", "soc_psychology"],
        "soc_globalization": ["soc_cold_war", "it_internet", "soc_capitalism"],
        "soc_digital_society": ["it_smartphone", "it_social_media", "it_internet"],
        "soc_social_media_rev": ["it_social_media", "soc_digital_society"],
        "soc_data_privacy": ["soc_digital_society", "it_big_data"],
    }

    # 补充遗漏的节点
    corrections["energy_natural_gas"] = ["energy_oil", "eng_pipeline", "energy_gas_turbine"]

    # 获取所有已知ID
    all_ids = {node["id"] for node in data}

    # 应用修正
    fixed_count = 0
    for node in data:
        nid = node["id"]
        if nid in corrections:
            new_prereqs = corrections[nid]
            # 过滤掉不存在的引用
            valid_prereqs = [p for p in new_prereqs if p in all_ids]
            node["prerequisites"] = valid_prereqs
            fixed_count += 1

    print(f"Fixed {fixed_count} nodes")

    # 检查未在corrections中出现的节点
    not_corrected = []
    for node in data:
        if node["id"] not in corrections:
            not_corrected.append(node["id"])
    if not_corrected:
        print(f"\nWARNING: {len(not_corrected)} nodes not in corrections list:")
        for nid in not_corrected:
            print(f"  {nid}")

    return data


def main() -> None:
    """主函数。"""
    print("Loading data...")
    data = load_data()
    print(f"Loaded {len(data)} nodes")

    print("\nFixing prerequisites...")
    data = fix_prerequisites(data)

    # 验证引用有效性
    print("\nValidating references...")
    ref_errors = validate_refs(data)
    if ref_errors:
        print(f"ERROR: {len(ref_errors)} invalid references:")
        for e in ref_errors:
            print(f"  {e}")
    else:
        print("All references valid ✓")

    # 验证无循环
    print("\nValidating no cycles...")
    if validate_no_cycles(data):
        print("No cycles detected ✓")
    else:
        print("ERROR: Cycles detected!")

    # 统计
    from collections import Counter
    prereq_counts = Counter(len(node["prerequisites"]) for node in data)
    print("\nPrerequisites distribution after fix:")
    for count, num in sorted(prereq_counts.items()):
        print(f"  {count} prerequisites: {num} nodes")

    # 保存
    print("\nSaving...")
    save_data(data)
    print("Done!")


if __name__ == "__main__":
    main()
