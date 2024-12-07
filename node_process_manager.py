import psutil
import os
import sys
import time

# 定义系统关键Node进程的关键字列表
PROTECTED_PROCESSES = [
    'system', 
    'windows',
    'service',
    # 可以继续添加其他关键进程标识
]

def is_protected_process(cmdline):
    """判断是否为受保护的系统Node进程"""
    if not cmdline:
        return False
    cmdline_str = ' '.join(cmdline).lower()
    return any(keyword in cmdline_str for keyword in PROTECTED_PROCESSES)

def list_node_processes():
    """列出所有Node进程"""
    print("\n当前运行的Node进程：")
    print("PID\t状态\t\t命令行")
    print("-" * 70)
    found = False
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status']):
        try:
            if proc.name().lower().startswith('node'):
                found = True
                cmdline = ' '.join(proc.cmdline()) if proc.cmdline() else '未知'
                protected = "（系统进程）" if is_protected_process(proc.cmdline()) else ""
                status = proc.status()
                print(f"{proc.pid}\t{status:<10}{cmdline} {protected}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    if not found:
        print("没有找到正在运行的Node进程")

def safe_kill_process(process):
    """安全地终止进程"""
    try:
        process.terminate()  # 先尝试温和地终止
        process.wait(timeout=3)  # 等待进程终止，最多3秒
    except psutil.TimeoutExpired:
        print(f"进程 {process.pid} 未能及时响应终止命令，尝试强制终止...")
        process.kill()  # 强制终止
    except Exception as e:
        print(f"终止进程时发生错误: {e}")
        return False
    return True

def kill_process(pid):
    """终止指定PID的进程"""
    try:
        process = psutil.Process(pid)
        if not process.name().lower().startswith('node'):
            print(f"PID {pid} 不是Node进程")
            return
        
        if is_protected_process(process.cmdline()):
            print(f"警告：PID {pid} 是系统Node进程，不能终止")
            return
            
        if safe_kill_process(process):
            print(f"已成功终止进程 PID: {pid}")
        
    except psutil.NoSuchProcess:
        print(f"找不到PID为 {pid} 的进程")
    except psutil.AccessDenied:
        print(f"没有权限终止PID为 {pid} 的进程")
    except Exception as e:
        print(f"发生未知错误: {e}")

def kill_all_node_processes():
    """终止所有非系统的Node进程"""
    killed = False
    skipped = False
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.name().lower().startswith('node'):
                if is_protected_process(proc.cmdline()):
                    print(f"跳过系统Node进程 PID: {proc.pid}")
                    skipped = True
                    continue
                    
                if safe_kill_process(proc):
                    killed = True
                    print(f"已终止进程 PID: {proc.pid}")
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    if not killed and not skipped:
        print("没有找到需要终止的Node进程")
    elif not killed and skipped:
        print("只发现了系统Node进程，已全部保留")

def main():
    if not os.geteuid() == 0:  # 在Unix系统上检查权限
        print("提示：以普通用户权限运行，可能无法终止某些进程")
        
    while True:
        try:
            print("\n请选择操作：")
            print("1. 查看所有Node进程")
            print("2. 关闭指定PID的Node进程")
            print("3. 关闭所有非系统Node进程")
            print("4. 退出")
            
            choice = input("\n请输入选项 (1-4): ").strip()
            
            if choice == '1':
                list_node_processes()
            elif choice == '2':
                pid = input("请输入要关闭的进程PID: ").strip()
                try:
                    pid = int(pid)
                    if pid <= 0:
                        print("请输入有效的正整数PID")
                        continue
                    kill_process(pid)
                except ValueError:
                    print("请输入有效的PID数字")
            elif choice == '3':
                confirm = input("确定要关闭所有非系统Node进程吗？(y/n): ").strip().lower()
                if confirm == 'y':
                    kill_all_node_processes()
            elif choice == '4':
                print("退出程序")
                sys.exit(0)
            else:
                print("无效的选项，请重新选择")
                
        except KeyboardInterrupt:
            print("\n程序被用户中断")
            sys.exit(1)
        except Exception as e:
            print(f"发生未知错误: {e}")
            continue

if __name__ == "__main__":
    main() 