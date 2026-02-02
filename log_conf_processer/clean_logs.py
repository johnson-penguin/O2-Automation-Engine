#!/usr/bin/env python3
"""
清理日誌檔案中的重複行
Clean duplicate lines in log files

此程式會掃描 templete_logs 目錄中的所有日誌檔案，
移除連續重複的行，每行最多保留兩次。

This program scans all log files in the templete_logs directory,
removes consecutive duplicate lines, keeping at most 2 occurrences.
"""

import os
from pathlib import Path
from typing import List


def clean_log_content(lines: List[str], max_consecutive: int = 2) -> List[str]:
    """
    清理日誌內容，移除連續重複的行
    
    Args:
        lines: 日誌行列表
        max_consecutive: 每行最多連續出現次數（預設為 2）
    
    Returns:
        清理後的日誌行列表
    """
    if not lines:
        return []
    
    cleaned_lines = []
    consecutive_count = 0
    previous_line = None
    
    for line in lines:
        if line == previous_line:
            consecutive_count += 1
            if consecutive_count < max_consecutive:
                cleaned_lines.append(line)
        else:
            consecutive_count = 0
            cleaned_lines.append(line)
            previous_line = line
    
    return cleaned_lines


def clean_log_file(log_path: Path, max_consecutive: int = 2, backup: bool = True) -> tuple:
    """
    清理單個日誌檔案
    
    Args:
        log_path: 日誌檔案路徑
        max_consecutive: 每行最多連續出現次數
        backup: 是否備份原始檔案
    
    Returns:
        (原始行數, 清理後行數) 的元組
    """
    if not log_path.exists():
        return (0, 0)
    
    # 讀取原始內容
    with open(log_path, 'r', encoding='utf-8') as f:
        original_lines = f.readlines()
    
    original_count = len(original_lines)
    
    # 清理內容（保留換行符）
    cleaned_lines = clean_log_content(original_lines, max_consecutive)
    cleaned_count = len(cleaned_lines)
    
    # 如果有變化，則更新檔案
    if original_count != cleaned_count:
        # 備份原始檔案
        if backup:
            backup_path = log_path.with_suffix(log_path.suffix + '.bak')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.writelines(original_lines)
        
        # 寫入清理後的內容
        with open(log_path, 'w', encoding='utf-8') as f:
            f.writelines(cleaned_lines)
    
    return (original_count, cleaned_count)


def clean_all_logs(logs_dir: Path, max_consecutive: int = 2, backup: bool = True) -> dict:
    """
    清理目錄中所有的日誌檔案
    
    Args:
        logs_dir: 日誌目錄路徑
        max_consecutive: 每行最多連續出現次數
        backup: 是否備份原始檔案
    
    Returns:
        統計資訊字典
    """
    stats = {
        'total_files': 0,
        'cleaned_files': 0,
        'total_original_lines': 0,
        'total_cleaned_lines': 0,
        'details': []
    }
    
    # 遍歷所有子目錄
    for case_dir in sorted(logs_dir.iterdir()):
        if not case_dir.is_dir():
            continue
        
        # 處理每個 case 目錄中的 log 檔案
        for log_file in ['cu.log', 'du.log', 'ue.log']:
            log_path = case_dir / log_file
            
            if log_path.exists():
                stats['total_files'] += 1
                original_count, cleaned_count = clean_log_file(log_path, max_consecutive, backup)
                
                stats['total_original_lines'] += original_count
                stats['total_cleaned_lines'] += cleaned_count
                
                removed_lines = original_count - cleaned_count
                if removed_lines > 0:
                    stats['cleaned_files'] += 1
                    stats['details'].append({
                        'file': str(log_path.relative_to(logs_dir.parent)),
                        'original': original_count,
                        'cleaned': cleaned_count,
                        'removed': removed_lines
                    })
    
    return stats


def main():
    """主函數"""
    # 設定路徑
    base_dir = Path(__file__).parent
    logs_dir = base_dir / "templete_logs"
    
    print("=" * 70)
    print("清理日誌檔案 / Cleaning log files")
    print("=" * 70)
    print(f"日誌目錄 / Logs directory: {logs_dir}")
    print(f"規則 / Rule: 每行最多連續出現 2 次 / Max 2 consecutive occurrences per line")
    print(f"備份 / Backup: 原始檔案會備份為 .bak / Original files backed up as .bak")
    print("=" * 70)
    
    if not logs_dir.exists():
        print(f"❌ 錯誤：目錄不存在 / Error: Directory does not exist")
        return
    
    # 執行清理
    print("\n開始清理... / Starting cleanup...")
    stats = clean_all_logs(logs_dir, max_consecutive=2, backup=True)
    
    # 顯示結果
    print("\n" + "=" * 70)
    print("清理結果 / Cleanup Results")
    print("=" * 70)
    print(f"總檔案數 / Total files processed: {stats['total_files']}")
    print(f"已清理檔案數 / Files cleaned: {stats['cleaned_files']}")
    print(f"原始總行數 / Total original lines: {stats['total_original_lines']:,}")
    print(f"清理後總行數 / Total cleaned lines: {stats['total_cleaned_lines']:,}")
    print(f"移除行數 / Lines removed: {stats['total_original_lines'] - stats['total_cleaned_lines']:,}")
    
    if stats['details']:
        print("\n詳細資訊 / Details:")
        print("-" * 70)
        for detail in stats['details']:
            reduction = detail['removed'] / detail['original'] * 100 if detail['original'] > 0 else 0
            print(f"  • {detail['file']}")
            print(f"    {detail['original']:,} → {detail['cleaned']:,} lines "
                  f"(-{detail['removed']:,}, {reduction:.1f}% reduction)")
    else:
        print("\n✨ 所有檔案都很乾淨，無需清理 / All files are clean, no cleanup needed")
    
    print("\n✅ 完成 / Done!")


if __name__ == "__main__":
    main()
