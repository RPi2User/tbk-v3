#!/usr/bin/env python3

import os
import argparse
import pathlib
import datetime
import subprocess
import xml.etree.ElementTree as ET

VERSION: str = "3.0"
DEBUG: bool = False

class File:

    def __init__(self, id: int, size: int, name: str, path: str, cksum: str = "", cksum_type: str = "") -> None:
        self.id: int = id
        self.size: int = size
        self.name: str = name
        self.path: str = path
        self.cksum: str = cksum
        self.cksum_type: str = cksum_type
    
    def __str__(self) -> str:
        return "File(ID: " + str(self.id) + ", Size: " + str(self.size) + ", Name: " + self.name + ", Path: " + self.path + ", cksum: " + self.cksum + ", cksum_type: " + self.cksum_type + ")\n"
    
class TableOfContent:
    
    def __init__(self, files: list[File], lto_version: str, optimal_blocksize: str, tape_sizeB: int, tbk_version: str, last_modified: str = "") -> None:
        self.files: list[File] = files      # List of all Files from TableOfContent
        self.ltoV: str = lto_version        # LTO-Version of Tape/Drive
        self.bs: str = optimal_blocksize    # Optimal Blocksize (only relevant for "dd")
        self.tape_size: int = tape_sizeB    # Constant, depends on LTO-Version
        self.tbkV: str = tbk_version        # Software-Version of Tape-Backup-Software from original TOC
        self.last_mod: str = last_modified  # Optional Timestamp (required for reading of tape)
        
    def __str__(self) -> str:
        return "TableOfContent(Files: " + str(self.files.__str__) + " LTO-Version: " + self.ltoV + " optimal Blocksize: " + self.bs + " Tape-Size: " + str(self.tape_size) + " TBK-Version" + self.tbkV + ")"
    
class TapeDrive:
    
    def __init__(self, path_to_tape_drive: str, blocksize: str) -> None:
        self.bs: str = blocksize
        self.drive_path: str = path_to_tape_drive
        self.rewind()
        
    def write(self, path_to_file: str, quiet: bool) -> None:
        _ec: int = 0    # Exit-Code
        if DEBUG:
            print("[DEBUG] debug@tbk:~ # dd if='" + path_to_file + "' of="+ self.drive_path + " bs=" + self.bs)
            print("Quiet: " + str(quiet))
            return
        if quiet:
            _ec = os.system("dd if='" + path_to_file + "' of="+ self.drive_path + " bs=" + self.bs + " 2>/dev/null")
        else:
            _ec = os.system("dd if='" + path_to_file + "' of="+ self.drive_path + " bs=" + self.bs + " status=progress")
        if _ec != 0:
            raise
        
    def read(self, path_to_file: str, quiet: bool) -> None:
        _ec: int = 0    # Exit-Code
        if DEBUG:
            print("[DEBUG] debug@tbk:~ # dd if=" + self.drive_path + " of='"+ path_to_file + "' bs=" + self.bs)
            print("[DEBUG] Quiet: " + str(quiet))
            return
        if quiet:
            _ec = os.system("dd if=" + self.drive_path + " of='"+ path_to_file + "' bs=" + self.bs + " 2>/dev/null")
        else:
            _ec = os.system("dd if=" + self.drive_path + " of='"+ path_to_file + "' bs=" + self.bs + " status=progress")
        if _ec != 0:
            raise

    def dump_toc(self) -> None:
        _ec: int = 0    # Exit-Code
        if DEBUG:
            print("[DEBUG] debug@tbk:~ # dd if=" + self.drive_path + " bs=" + self.bs + " | cat ")
        else:
            _ec = os.system("dd if=" + self.drive_path + " bs=" + self.bs + " | cat ")

        if _ec != 0:
            raise

    def rewind(self) -> None:
        if DEBUG:
            print("[DEBUG] debug@tbk:~ # mt -f " + self.drive_path + " rewind")
        else:
            os.system("mt -f " + self.drive_path + " rewind")
        
    def eject(self) -> None:
        if DEBUG:
            print("[DEBUG] debug@tbk:~ # mt -f " + self.drive_path + " eject")
        else:
            os.system("mt -f " + self.drive_path + " eject")

class MainProgram:
    
    dry_run: bool = False
    cksum: bool = False
    
    def __init__(self, path_to_tape_drive: str, default_blocksize: str) -> None:
        self.tape_drive: TapeDrive = TapeDrive(path_to_tape_drive=path_to_tape_drive, blocksize=default_blocksize)
        if DEBUG:
            self.debug_dummy()
        
    def debug_dummy(self) -> None:
        files: list[File] = [File(1, 1230, "Testfile", "/opt/test"), File(2, 54666666, "file.satan", "/asd", "0x00123456", "md5")]
        self.toc: TableOfContent = TableOfContent(files, "3", "384k", 400000000000, VERSION, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))

    def argparser(self) -> None:
        parser = argparse.ArgumentParser(
            prog="tbk",
            description="Software zur Steuerung von Bandlaufwerken der dritten Version")

        parser.add_argument("-w", "--write", 
                            type=lambda p: pathlib.Path(p).absolute(),
                            nargs='?',
                            help="Write Files of Directory to Tape")
        parser.add_argument("-r", "--read", 
                            type=lambda p: pathlib.Path(p).absolute(),
                            nargs='?', 
                            help="Read Content to Directory")
        parser.add_argument("-l", "--list",
                            help="List Contents of Tape",
                            action="store_true")
        parser.add_argument("-d", "--dump",
                            help="Dumps Table Of Content from Tape",
                            action="store_true")
        parser.add_argument("-D", "--dry-run",
                            help="Shows Summaries but does not Read / Write",
                            action="store_true")
        parser.add_argument("-c", "--checksum",
                            help="Enable md5sum checking at write / read",
                            action="store_true")
        
        _args: argparse.Namespace = parser.parse_args()
        
        if DEBUG:
            print("[DEBUG] ARGS: " + str(_args))
            
        if _args.dump:
            self.dumpTOC()
            exit(0)
        if _args.dry_run:
            self.dry_run = True
        if _args.checksum:
            self.cksum = True
        if _args.list:
            self.showTOC(self.readTOC())
            exit(0)
        if _args.write != None:
            self.write(str(_args.write))
            exit(0)
        if _args.read != None:
            self.read(str(_args.read))
            exit(0)

    def write(self, src_path: str) -> None:
        self.toc: TableOfContent = TableOfContent(files=self.getFilesFromDir(src_path),
                                                  lto_version="3", 
                                                  optimal_blocksize="384k", 
                                                  tape_sizeB=400000000000, 
                                                  tbk_version=VERSION,
                                                  last_modified=str(datetime.datetime.now()))
        self.showTOC(self.toc)
        if input("Do you want to write those Files to tape? [y/N] (y) ") == "N" or self.dry_run:
                exit(0)
        if self.cksum:
            for index, file in enumerate(self.toc.files):
                print("[ " + str(index+1) + " / " + str(len(self.toc.files)) + " ] [CKSUM] Generating checksum (md5): (" + self.convertHRSize(float(file.size)) + ") Name: " + file.path)
                file.cksum = self.createCksum(file.path)
                file.cksum_type = "md5"
        self.writeTOC(self.toc)
        print("--------------------------------------------------")
        for index, file in enumerate(self.toc.files):
            print("[ " + str(index+1) + " / " + str(len(self.toc.files)) + " ] [WRITE] (" + self.convertHRSize(float(file.size)) + ") Name: " + file.path)
            self.tape_drive.write(file.path, False)
        self.tape_drive.rewind()
        print("Write complete: Ejecting Tape.")
        self.tape_drive.eject()
        
    
    def getFilesFromDir(self, src_path: str) -> list[File]:
        _out: list[File] = []
        try:
            for index, path in enumerate(os.listdir(path=src_path)):
                full_path: str = src_path + "/" + path
                _out.append(File(id=index,
                            size=os.path.getsize(full_path),
                            name=path,
                            path=full_path
                            ))
        except:
            print("[ERROR] Cannot Read Source-Directory: Invalid path!")
            exit(1)
        return _out
    
    def read(self, dest_path: str) -> None:
        self.toc = self.readTOC()
        self.showTOC(self.toc)
        if input("Do you want to restore to " + dest_path + "? [y/N] (y) ") == "N" or self.dry_run:
            exit(0)
        try: 
            os.mkdir(dest_path)
        except:
            pass
        for index, file in enumerate(self.toc.files):
            restore_path: str = dest_path + "/" + file.name
            print("[ " + str(index+1) + " / " + str(len(self.toc.files)) + " ] [READ] (" + self.convertHRSize(float(file.size)) + ") Name: " + restore_path)
            self.tape_drive.read(restore_path, False)
            if self.cksum:
                print("[ " + str(index+1) + " / " + str(len(self.toc.files)) + " ] [CKSUM] (" + self.convertHRSize(float(file.size)) + ") Checking " + restore_path)
                cksum: str = self.createCksum(restore_path)
                if file.cksum != cksum:
                    print("[ERROR] Checksum Error at restore: Checksum mismatch at File: " + restore_path)
                    print("     Original Checksum: " + file.cksum)
                    print("     Current Checksum:  " + cksum)
                    exit(1)
        self.tape_drive.rewind()
        print("Read complete: Ejecting Tape.")
        self.tape_drive.eject()
        
       
    def dumpTOC(self) -> None:
        self.tape_drive.rewind()
        self.tape_drive.dump_toc()
        self.tape_drive.rewind()
        
    def showTOC(self, toc: TableOfContent) -> None:
        print("\n--- TAPE INFORMATION ---\n")
        print("- TBK-Version:\t" + toc.tbkV)
        print("- LTO-Version:\t" + toc.ltoV)
        print("- Blocksize:\t" + toc.bs)
        print("- Tape-Size:\t" + self.convertHRSize(float(toc.tape_size)))
        print("\nLast Modified:\t" + toc.last_mod)
        print("\n*")
        _remaining: int = toc.tape_size
        for file in toc.files:
            print("├─┬ \x1b[96m" + file.name + "\x1b[0m")
            print("│ ├── Size:\t" + self.convertHRSize(float(file.size)))
            print("│ └── Checksum:\t" + file.cksum)
            print("│")
            _remaining -= file.size
        print("│")
        print("└ \x1b[93m" + self.convertHRSize(float(_remaining)) + "\x1b[0m Remaining")
        
    def writeTOC(self, toc: TableOfContent) -> int:
        # Create suitable Filename + Path
        _xml_path: str = "/tmp/"+ datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_toc.tmp"
        # Create XML and write to Path
        self.toc2xml(toc=toc, export_path=_xml_path)
        # Write XML from Path to Tape
        self.tape_drive.write(_xml_path, True)
        # Remove Temp-File
        if DEBUG != True:
            pass
            os.remove(_xml_path)
        return 0
    
    def readTOC(self) -> TableOfContent:
        # Steps:
        # 1. Read XML-File from Tape to /tmp/read-timestamp.tmp
        # 2. Parse XML-File into ET.ElementTree
        # 3. Create TOC-Object, delete temporary File
        # 4. Return toc
        _xml_path: str = "/tmp/"+ datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_toc-read.tmp"
        self.tape_drive.rewind()
        self.tape_drive.read(_xml_path, True)
        _out: TableOfContent = self.xml2toc(_xml_path)
        os.remove(_xml_path)
        return _out

    def toc2xml(self, toc: TableOfContent, export_path: str) -> None:
        # Create XML-Root
        root = ET.Element("toc")
        # Append Header
        header: ET.Element = ET.SubElement(root, "header")
        ET.SubElement(header, "lto-version").text = toc.ltoV
        ET.SubElement(header, "optimal-blocksize").text = toc.bs
        ET.SubElement(header, "tape-size").text = str(toc.tape_size)
        ET.SubElement(header, "tbk-version").text = VERSION
        ET.SubElement(header, "last-modified").text = str(datetime.datetime.now())
        # Append Files
        for entry in toc.files:
            file: ET.Element = ET.SubElement(root, "file")
            ET.SubElement(file, "id").text = str(entry.id)
            ET.SubElement(file, "filename").text = entry.name
            ET.SubElement(file, "complete-path").text = entry.path
            ET.SubElement(file, "size").text = str(entry.size)
            ET.SubElement(file, "type").text = entry.cksum_type
            ET.SubElement(file, "value").text = entry.cksum
        
        xml_tree: ET.ElementTree = ET.ElementTree(element=root)
        try: 
            ET.indent(tree=xml_tree)
            xml_tree.write(file_or_filename=export_path, encoding="utf-8")
        except:
            raise NameError("[ERROR] Could not save Table of Contents!")

    def xml2toc(self, path_to_xml: str) -> TableOfContent:
        self.tape_drive.rewind()
        # Read XML from Tape
        self.tape_drive.read(path_to_file=path_to_xml, quiet=True)
        # Try to parse File
        try:
            xml_root: ET.Element = ET.parse(source=path_to_xml).getroot()
        except:
            print("[ERROR] Could not parse Table of Contents: Invalid Format")
            exit(1)
        files: list[File] = []
        for index in range(1, len(xml_root)):
            try:                
                files.append(File(id=int(str(xml_root[index][0].text)),
                                name=str(xml_root[index][1].text),
                                path=str(xml_root[index][2].text),
                                size=int(str(xml_root[index][3].text)),
                                cksum_type=str(xml_root[index][4].text),
                                cksum=str(xml_root[index][5].text)
                ))
            except:
                files.append(File(id=int(str(xml_root[index][0].text)),
                                name=str(xml_root[index][1].text),
                                path=str(xml_root[index][2].text),
                                size=int(str(xml_root[index][3].text))
                ))
        _out: TableOfContent = TableOfContent(
            files=files,
            lto_version=str(xml_root[0][0].text),
            optimal_blocksize=str(xml_root[0][1].text),
            tape_sizeB=int(str(xml_root[0][2].text)),
            tbk_version=str(xml_root[0][3].text),
            last_modified=str(xml_root[0][4].text)
        )
        return _out

    def createCksum(self, path_to_file: str) -> str:
        _out: str = str(subprocess.check_output("md5sum '" + path_to_file + "' | awk '{ print $1}'", shell=True))
        _out = _out.split("'", 2)[1].split("\\", 1)[0]
        return _out

    def convertHRSize(self, num: float, suffix="B") -> str:
        for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
            if abs(num) < 1024.0:
                return f"{num:3.1f} {unit}{suffix}"
            num /= 1024.0
        return f"{num:.1f}Yi{suffix}"

def main() -> int:
    mp: MainProgram = MainProgram("/dev/nst0", "384k")
    mp.argparser()
    return 0

if __name__ == '__main__':
    exit(main())
