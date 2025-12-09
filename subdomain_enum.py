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
        # Ejecutamos el comando. Usamos shell=True para permitir pipes y redirecciones.
        # Redirigimos stdout y stderr para mantener la barra de progreso limpia, 
        # a menos que sea crítico ver el output.
        subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        # Si falla, no interrumpimos todo el script, pero notificamos (opcionalmente)
        # print(f"\n[!] Error ejecutando {description}")
        pass

def main():
    if len(sys.argv) != 2:
        print("Uso: python3 subdomain_enum.py <target.com>")
        sys.exit(1)

    target = sys.argv[1]
    
    # Definimos los comandos a ejecutar
    # Nota: Se asume que las herramientas están instaladas y en el PATH.
    commands = [
        (f"subfinder -d {target} -all -silent -o subfinder-rescursive.txt", "subfinder"),
        (f"findomain --quiet -t {target} > findomain.txt", "findomain"), # Cambiado tee por > para evitar output en consola
        (f"assetfinder -subs-only {target} > assetfinder.txt", "assetfinder"), # Cambiado tee por > para evitar output en consola
        (f"sublist3r -d {target} -t 50 -o sublist3r.txt", "sublist3r"),
        (f'curl -s "https://crt.sh/?q=%25.{target}&output=json" | jq -r \'.[].name_value\' | sed \'s/\*\.//g\' > "crtsh.txt"', "crt.sh")
    ]

    # Pasos: Comandos + Unificar + HTTPX + Limpieza
    total_steps = len(commands) + 3 
    current_step = 0

    print(f"[*] Iniciando enumeración para: {target}")
    print_progress(current_step, total_steps, prefix='Progreso:', suffix='Iniciando...', length=40)

    # 1. Ejecutar herramientas de enumeración
    for cmd, desc in commands:
        current_step += 1
        print_progress(current_step, total_steps, prefix='Progreso:', suffix=f'Ejecutando {desc}' + ' '*10, length=40)
        run_command(cmd, desc)

    # 2. Agrupar y eliminar duplicados
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
    
    # 3. Comprobar dominios vivos con httpx
    current_step += 1
    print_progress(current_step, total_steps, prefix='Progreso:', suffix='Ejecutando httpx (sudo)' + ' '*5, length=40)
    
    # Nota: sudo pedirá contraseña si no está configurado NOPASSWD.
    # Para que el usuario pueda escribir la contraseña, no ocultamos stdout/stderr aquí si es interactivo,
    # pero como queremos mantener la barra, es complicado. 
    # Lo ejecutaremos normal, si pide pass, el usuario lo verá.
    httpx_cmd = "cat subdomains.txt | sudo httpx > alive_subdomains.txt"
    try:
        subprocess.run(httpx_cmd, shell=True, check=True)
    except subprocess.CalledProcessError:
        print("\n[!] Error ejecutando httpx. Asegúrate de tener permisos sudo o que httpx esté instalado.")

    # 4. Limpieza de archivos temporales
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
