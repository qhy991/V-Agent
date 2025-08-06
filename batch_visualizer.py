#!/usr/bin/env python3
"""
批量可视化器 - 处理多个实验目录
Batch Visualizer - Process multiple experiment directories
"""

import os
import glob
import argparse
from pathlib import Path
from html_visualizer import HTMLVisualizer

def find_experiments(base_dir, pattern="*"):
    """查找所有实验目录"""
    base_path = Path(base_dir)
    if not base_path.exists():
        print(f"❌ 基础目录不存在: {base_dir}")
        return []
    
    # 查找所有匹配的实验目录
    experiment_patterns = [
        f"{pattern}",
        f"llm_experiments/{pattern}",
        f"experiments/{pattern}",
        f"**/{pattern}"
    ]
    
    experiments = []
    for exp_pattern in experiment_patterns:
        experiments.extend(glob.glob(str(base_path / exp_pattern)))
    
    # 过滤出目录
    experiments = [Path(exp) for exp in experiments if Path(exp).is_dir()]
    
    # 去重并排序
    experiments = sorted(set(experiments), key=lambda x: x.stat().st_mtime, reverse=True)
    
    return experiments

def process_experiment(experiment_path, output_dir, config_file=None, verbose=True):
    """处理单个实验"""
    try:
        if verbose:
            print(f"\n🔄 处理实验: {experiment_path.name}")
        
        # 创建实验特定的输出目录
        experiment_output_dir = Path(output_dir) / experiment_path.name
        experiment_output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建可视化器
        visualizer = HTMLVisualizer(
            experiment_path=str(experiment_path),
            output_dir=str(experiment_output_dir),
            config_file=config_file
        )
        
        # 生成报告
        output_file = visualizer.generate_html_report()
        
        if verbose:
            print(f"✅ 完成: {output_file}")
        
        return {
            'experiment': experiment_path.name,
            'status': 'success',
            'output_file': output_file,
            'path': str(experiment_path)
        }
        
    except Exception as e:
        if verbose:
            print(f"❌ 失败: {experiment_path.name} - {e}")
        
        return {
            'experiment': experiment_path.name,
            'status': 'failed',
            'error': str(e),
            'path': str(experiment_path)
        }

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="批量生成V-Agent实验可视化HTML报告")
    parser.add_argument("--base-dir", type=str, default=".", help="基础目录，默认为当前目录")
    parser.add_argument("--pattern", type=str, default="llm_coordinator_*", help="实验目录模式")
    parser.add_argument("--output-dir", type=str, default="./batch_reports", help="输出目录")
    parser.add_argument("--config-file", type=str, help="配置文件路径")
    parser.add_argument("--max-experiments", type=int, help="最大处理实验数量")
    parser.add_argument("--verbose", action="store_true", help="显示详细输出")
    parser.add_argument("--dry-run", action="store_true", help="仅显示将要处理的实验，不实际处理")
    
    args = parser.parse_args()
    
    print("🎯 开始批量生成V-Agent实验可视化HTML报告...")
    print(f"📁 基础目录: {args.base_dir}")
    print(f"🔍 搜索模式: {args.pattern}")
    print(f"📤 输出目录: {args.output_dir}")
    
    # 查找实验
    experiments = find_experiments(args.base_dir, args.pattern)
    
    if not experiments:
        print("❌ 未找到任何实验目录")
        return
    
    print(f"\n📊 找到 {len(experiments)} 个实验目录:")
    for i, exp in enumerate(experiments[:10], 1):  # 只显示前10个
        print(f"  {i}. {exp.name}")
    
    if len(experiments) > 10:
        print(f"  ... 还有 {len(experiments) - 10} 个实验")
    
    # 限制处理数量
    if args.max_experiments:
        experiments = experiments[:args.max_experiments]
        print(f"\n⚠️ 限制处理数量为: {args.max_experiments}")
    
    if args.dry_run:
        print(f"\n🔍 干运行模式 - 将处理 {len(experiments)} 个实验")
        return
    
    # 创建输出目录
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 处理实验
    results = []
    success_count = 0
    failed_count = 0
    
    for i, experiment in enumerate(experiments, 1):
        print(f"\n[{i}/{len(experiments)}] 处理实验: {experiment.name}")
        
        result = process_experiment(
            experiment, 
            args.output_dir, 
            args.config_file, 
            args.verbose
        )
        
        results.append(result)
        
        if result['status'] == 'success':
            success_count += 1
        else:
            failed_count += 1
    
    # 生成汇总报告
    summary_file = output_path / "batch_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("批量可视化处理汇总报告\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"处理时间: {Path().stat().st_mtime}\n")
        f.write(f"基础目录: {args.base_dir}\n")
        f.write(f"搜索模式: {args.pattern}\n")
        f.write(f"输出目录: {args.output_dir}\n")
        f.write(f"配置文件: {args.config_file or '默认配置'}\n\n")
        
        f.write(f"总计实验: {len(experiments)}\n")
        f.write(f"成功处理: {success_count}\n")
        f.write(f"处理失败: {failed_count}\n")
        f.write(f"成功率: {success_count/len(experiments)*100:.1f}%\n\n")
        
        f.write("详细结果:\n")
        f.write("-" * 30 + "\n")
        
        for result in results:
            f.write(f"实验: {result['experiment']}\n")
            f.write(f"状态: {result['status']}\n")
            if result['status'] == 'success':
                f.write(f"输出: {result['output_file']}\n")
            else:
                f.write(f"错误: {result['error']}\n")
            f.write(f"路径: {result['path']}\n")
            f.write("\n")
    
    # 输出汇总
    print(f"\n🎉 批量处理完成!")
    print(f"📊 汇总:")
    print(f"  总计实验: {len(experiments)}")
    print(f"  成功处理: {success_count}")
    print(f"  处理失败: {failed_count}")
    print(f"  成功率: {success_count/len(experiments)*100:.1f}%")
    print(f"📄 汇总报告: {summary_file}")
    print(f"📁 输出目录: {args.output_dir}")

if __name__ == "__main__":
    main() 