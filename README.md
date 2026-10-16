# Windows Storage Tools

两个只读的本地磁盘检查脚本，使用 Python 标准库，建议 Python 3.10+。不会迁移、删除文件或更改系统配置。

```powershell
python folder_storage_scan.py --root "D:\Projects" --output reports/folder-storage-scan.json.gz
python migration_inventory.py --root "D:\Projects" --output-dir reports
```

- `folder_storage_scan.py`：统计目录大小、文件数和按文件标识去重后的字节数；跳过重解析点，写出 gzip JSON。
- `migration_inventory.py`：统计目录大小及文件数，同时记录符号链接/重解析点的目标，不遍历目标。可重复传入 `--root`，建议使用彼此不重叠的目录。
- 未指定 `--root` 时扫描当前用户主目录。大目录可能需要较长时间；无法访问的路径记入 `errors`。

统计口径是文件逻辑大小，不等于磁盘实际占用、压缩后的大小或可清理容量。报告包含本机路径，请只在本机保存；`reports/` 已加入忽略列表。本仓库不包含扫描结果和针对某台电脑的迁移决策。

[MIT](LICENSE)
