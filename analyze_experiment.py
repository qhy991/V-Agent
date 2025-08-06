#!/usr/bin/env python3
"""
实验分析脚本
Experiment Analysis Script
=========================

使用增强日志记录系统分析实验结果的示例脚本。
"""

import argparse
import sys
from pathlib import Path
import json
import logging

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.enhanced_experiment_logger import EnhancedExperimentLogger
from core.conversation_analyzer import ConversationAnalyzer


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('experiment_analysis.log')
        ]
    )


def analyze_existing_experiment(report_path: str, output_dir: str = None):
    """分析已有的实验报告"""
    report_path = Path(report_path)
    
    if not report_path.exists():
        print(f"❌ 实验报告文件不存在: {report_path}")
        return
        
    if output_dir is None:
        output_dir = report_path.parent
    else:
        output_dir = Path(output_dir)
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🔍 分析实验报告: {report_path}")
    
    # 创建对话分析器
    analyzer = ConversationAnalyzer(str(report_path))
    
    # 执行分析
    print("📊 执行对话分析...")
    analysis_report = analyzer.analyze()
    
    # 保存分析结果
    analysis_path = analyzer.save_analysis(analysis_report, output_dir / "conversation_analysis.json")
    
    # 生成文本摘要
    summary_text = analyzer.generate_summary_text(analysis_report)
    summary_path = output_dir / "analysis_summary.md"
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_text)
        
    print(f"✅ 分析完成!")
    print(f"   📄 详细分析: {analysis_path}")
    print(f"   📝 文本摘要: {summary_path}")
    
    # 显示关键发现
    print(f"\n🎯 关键发现:")
    print(f"   📞 总LLM调用: {analysis_report.conversation_stats.get('total_llm_calls', 0)}次")
    print(f"   ✅ 成功率: {analysis_report.conversation_stats.get('successful_calls', 0) / max(analysis_report.conversation_stats.get('total_llm_calls', 1), 1) * 100:.1f}%")
    print(f"   ⏱️ 平均响应: {analysis_report.conversation_stats.get('average_call_duration', 0):.2f}秒")
    print(f"   🤖 参与智能体: {analysis_report.conversation_stats.get('unique_agents', 0)}个")
    print(f"   🔍 识别模式: {len(analysis_report.identified_patterns)}个")
    print(f"   ⚠️ 发现问题: {len(analysis_report.problem_diagnosis)}个")
    print(f"   💡 改进建议: {len(analysis_report.improvement_recommendations)}个")
    
    # 显示高优先级建议
    high_priority_recommendations = [r for r in analysis_report.improvement_recommendations if r.get('priority') in ['critical', 'high']]
    if high_priority_recommendations:
        print(f"\n🚨 高优先级建议:")
        for i, rec in enumerate(high_priority_recommendations[:3], 1):
            print(f"   {i}. {rec['title']} ({rec['priority']})")
            
    return analysis_report


def create_enhanced_experiment_report(experiment_data: dict, output_dir: str):
    """创建增强的实验报告"""
    experiment_id = experiment_data.get('experiment_id', 'unknown')
    output_path = Path(output_dir)
    
    print(f"📋 创建增强实验报告: {experiment_id}")
    
    # 创建增强实验记录器
    logger = EnhancedExperimentLogger(experiment_id, output_path)
    
    # 设置任务信息
    logger.set_task_description(experiment_data.get('task_description', ''))
    logger.mark_success(experiment_data.get('success', False))
    
    # 生成详细报告
    print("📊 生成详细报告...")
    detailed_report = logger.generate_detailed_report()
    
    # 保存报告
    report_path = logger.save_report(detailed_report)
    
    print(f"✅ 增强报告已创建: {report_path}")
    
    return report_path


def compare_experiments(report_paths: list, output_dir: str = "comparison"):
    """比较多个实验"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🔍 比较 {len(report_paths)} 个实验...")
    
    analyzers = []
    reports = []
    
    for path in report_paths:
        if not Path(path).exists():
            print(f"⚠️ 跳过不存在的文件: {path}")
            continue
            
        analyzer = ConversationAnalyzer(path)
        analysis_report = analyzer.analyze()
        
        analyzers.append(analyzer)
        reports.append(analysis_report)
        
    if not reports:
        print("❌ 没有有效的实验报告进行比较")
        return
        
    # 生成比较报告
    comparison = {
        "comparison_timestamp": __import__('time').time(),
        "experiments": [],
        "summary_comparison": {},
        "recommendations": []
    }
    
    for report in reports:
        stats = report.conversation_stats
        comparison["experiments"].append({
            "experiment_id": report.experiment_id,
            "total_llm_calls": stats.get('total_llm_calls', 0),
            "success_rate": stats.get('successful_calls', 0) / max(stats.get('total_llm_calls', 1), 1),
            "average_duration": stats.get('average_call_duration', 0),
            "total_tokens": stats.get('total_tokens', 0),
            "unique_agents": stats.get('unique_agents', 0),
            "problems_count": len(report.problem_diagnosis),
            "patterns_count": len(report.identified_patterns)
        })
        
    # 计算聚合统计
    if comparison["experiments"]:
        exp_data = comparison["experiments"]
        comparison["summary_comparison"] = {
            "best_success_rate": max(exp["success_rate"] for exp in exp_data),
            "worst_success_rate": min(exp["success_rate"] for exp in exp_data),
            "fastest_average_duration": min(exp["average_duration"] for exp in exp_data),
            "slowest_average_duration": max(exp["average_duration"] for exp in exp_data),
            "most_efficient_experiment": min(exp_data, key=lambda x: x["average_duration"])["experiment_id"],
            "most_successful_experiment": max(exp_data, key=lambda x: x["success_rate"])["experiment_id"]
        }
        
    # 保存比较结果
    comparison_path = output_dir / "experiment_comparison.json"
    with open(comparison_path, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2, default=str)
        
    print(f"✅ 比较报告已保存: {comparison_path}")
    
    # 显示比较摘要
    print(f"\n📊 比较摘要:")
    summary = comparison["summary_comparison"]
    if summary:
        print(f"   🏆 最高成功率: {summary['best_success_rate']*100:.1f}% ({summary['most_successful_experiment']})")
        print(f"   ⚡ 最快响应: {summary['fastest_average_duration']:.2f}秒 ({summary['most_efficient_experiment']})")
        print(f"   📈 成功率范围: {summary['worst_success_rate']*100:.1f}% - {summary['best_success_rate']*100:.1f}%")
        
    return comparison_path


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="实验分析工具")
    parser.add_argument("command", choices=["analyze", "enhance", "compare"], help="执行的命令")
    parser.add_argument("--report", "-r", help="实验报告文件路径")
    parser.add_argument("--reports", "-rs", nargs="+", help="多个实验报告文件路径（用于比较）")
    parser.add_argument("--output", "-o", help="输出目录", default="analysis_output")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    setup_logging()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    try:
        if args.command == "analyze":
            if not args.report:
                print("❌ 请提供 --report 参数")
                return
                
            analyze_existing_experiment(args.report, args.output)
            
        elif args.command == "enhance":
            if not args.report:
                print("❌ 请提供 --report 参数")
                return
                
            # 读取原始实验数据
            with open(args.report, 'r', encoding='utf-8') as f:
                experiment_data = json.load(f)
                
            enhanced_path = create_enhanced_experiment_report(experiment_data, args.output)
            
            # 自动分析增强后的报告
            print("🔄 自动分析增强报告...")
            analyze_existing_experiment(str(enhanced_path), args.output)
            
        elif args.command == "compare":
            if not args.reports or len(args.reports) < 2:
                print("❌ 请提供至少2个 --reports 参数")
                return
                
            compare_experiments(args.reports, args.output)
            
    except KeyboardInterrupt:
        print("\n❌ 用户中断操作")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()