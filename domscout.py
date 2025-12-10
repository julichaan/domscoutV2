import subprocess
import sys
import os

def print_progress(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    if iteration == total: 
        print()

def run_command(command, description):
    try:
        subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        pass

def print_banner():
    print(r"""
  ____                  ____                   _       ,_,
 |  _ \  ___  _ __ ___ / ___|  ___ ___  _   _| |_     (O,O)
 | | | |/ _ \| '_ ` _ \\___ \ / __/ _ \| | | | __|    (   )
 | |_| | (_) | | | | | |___) | (_| (_) | |_| | |_     -"-"-
 |____/ \___/|_| |_| |_|____/ \___\___/ \__,_|\__|
                                                  """)
    print(" Author: julichaan")
    print(" Version: 1.0")
    print("-" * 50)

def main():
    print_banner()
    if len(sys.argv) != 2:
        print("Uso: python3 subdomain_enum.py <target.com>")
        sys.exit(1)

    target = sys.argv[1]
    
    commands = [
        (f"subfinder -d {target} -all -silent -o subfinder-rescursive.txt", "subfinder"),
        (f"findomain --quiet -t {target} > findomain.txt", "findomain"),
        (f"assetfinder -subs-only {target} > assetfinder.txt", "assetfinder"),
        (f"sublist3r -d {target} -t 50 -o sublist3r.txt", "sublist3r"),
        (f'curl -s "https://crt.sh/?q=%25.{target}&output=json" | jq -r \'.[].name_value\' | sed \'s/\*\.//g\' > "crtsh.txt"', "crt.sh")
    ]

    total_steps = len(commands) + 3 
    current_step = 0

    print(f"[*] Iniciando enumeración para: {target}")
    print_progress(current_step, total_steps, prefix='Progreso:', suffix='Iniciando...', length=40)

    for cmd, desc in commands:
        current_step += 1
        print_progress(current_step, total_steps, prefix='Progreso:', suffix=f'Ejecutando {desc}' + ' '*10, length=40)
        run_command(cmd, desc)

    current_step += 1
    print_progress(current_step, total_steps, prefix='Progreso:', suffix='Procesando resultados' + ' '*5, length=40)
    
    filenames = ["subfinder-rescursive.txt", "findomain.txt", "assetfinder.txt", "sublist3r.txt", "crtsh.txt"]
    unique_subdomains = set()

    for filename in filenames:
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        clean_line = line.strip()
                        if clean_line:
                            unique_subdomains.add(clean_line)
            except Exception:
                pass

    with open("subdomains.txt", "w") as f:
        for subdomain in sorted(unique_subdomains):
            f.write(f"{subdomain}\n")
    
    current_step += 1
    print_progress(current_step, total_steps, prefix='Progreso:', suffix='Ejecutando httpx (sudo)' + ' '*5, length=40)
    

    httpx_cmd = "cat subdomains.txt | sudo httpx > alive_subdomains.txt"
    try:
        subprocess.run(httpx_cmd, shell=True, check=True)
    except subprocess.CalledProcessError:
        print("\n[!] Error ejecutando httpx. Asegúrate de tener permisos sudo o que httpx esté instalado.")

    current_step += 1
    print_progress(current_step, total_steps, prefix='Progreso:', suffix='Limpiando archivos' + ' '*10, length=40)
    
    files_to_remove = filenames + ["subdomains.txt"]
    for filename in files_to_remove:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except OSError:
                pass
    
    print_progress(total_steps, total_steps, prefix='Progreso:', suffix='Completado!' + ' '*15, length=40)
    print(f"\n\n[+] Proceso finalizado. Resultados guardados en 'alive_subdomains.txt'.")

if __name__ == "__main__":
    main()
