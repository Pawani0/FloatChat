from ftplib import FTP
import os

ftp = FTP("ftp.ifremer.fr")
ftp.login()
for y in range(2000, 2025):
    for i in range(13):
        month_folder = f"{i+1:02d}"
        ftp.cwd(f"ifremer/argo/geo/indian_ocean/{y}/{month_folder}")
        # List files in directory
        files = ftp.nlst()
        print(f"Total files in {month_folder}-{y}: {len(files)}")
        # Create local month folder if it doesn't exist
        if not os.path.exists(month_folder):
            os.makedirs(month_folder)
        for file in files:
            local_path = os.path.join(month_folder, file)
            with open(local_path, "wb") as f:
                ftp.retrbinary(f"RETR {file}", f.write)

ftp.quit()