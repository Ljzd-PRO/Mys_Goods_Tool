# 在 iOS iSH 上使用本程序的方法
## 1⃣️ 安装
从 App Store 下载安装 [🔗iSH Shell](https://apps.apple.com/us/app/ish-shell/id1436902243)

<img src="https://user-images.githubusercontent.com/63289359/180285123-374ca4af-d4ee-400c-bdee-ed16badb5e1c.jpg" alt="IMG_0841"/>


## 2⃣️ 导入文件
1. 若安装后还未打开过iSH App，先打开一次。
2. 打开 文件 App，切换到“浏览”，点击右上角的三个点，点击“编辑”，勾选“位置”中的“iSH”，点击“完成”。

<div>
  <img src="https://user-images.githubusercontent.com/63289359/180287295-c0d5e6fd-a01b-4c5e-8484-4ddef20977e7.jpg" alt="IMG_0842"/>
  <img src="https://user-images.githubusercontent.com/63289359/180288351-d6f6135e-a811-40e8-bd33-219acca0a82d.jpg" alt="IMG_0843"/>
<div/>
  
3. 解压从 [🔗release](https://github.com/Ljzd-PRO/Mys_Goods_Tool/releases) 下载的 Alpine-iSH-i686 构建版。
<img src="https://user-images.githubusercontent.com/63289359/180286945-adb132bb-0cb2-445b-8c25-c7115266338e.jpg" alt="IMG_0844"/>
  
4. 移动解压后的文件夹到 `iSH/root/` 即可。
  
<div>
  <img src="https://user-images.githubusercontent.com/63289359/180289220-1ef4eea4-8415-4c70-9d24-183b7bd06204.PNG" alt="IMG_0845"/>
  <img src="https://user-images.githubusercontent.com/63289359/180289047-232539c5-6ce4-425b-acbb-34287aeac102.PNG" alt="IMG_0846"/>
<div/>


## 3⃣️ 运行程序
1. 打开 iSH App，进入程序所在目录  
- 输入 `ls` 查看当前目录下的所有文件  
- 输入 `cd <目录>` 进入目录  
(由于长度和特殊符号，不建议完整键入文件/文件夹名称，按 `TAB` 键 (输入法键盘上端有虚拟按键) 即可自动补全)

2. 给程序赋予执行权限。
- 使用命令：
```shell
chmod 777 main tool
```
  
3. 执行程序。
- 运行 `tool`：
```shell
./tool
```
- 运行 `main`：
```shell
./main
```

其他：
- 按 `CTRL` + `C` 可强制结束程序
- 目前似乎有Bug，程序运行时无法长按屏幕复制其中文字，不然会导致程序退出

<div>
  <img src="https://user-images.githubusercontent.com/63289359/180294285-8ec29b64-096a-41d6-ae9c-92a6972978e9.PNG" alt="IMG_0853"/>
  <img src="https://user-images.githubusercontent.com/63289359/180294292-3155f24e-8118-4ca0-96d4-a43b2de11983.PNG" alt="IMG_0854"/>
<div/>
  
  
## 4⃣️ 编辑和查看配置文件、日志
在 文件 App - 浏览 中，进入 iSH 目录，进入程序所在目录
- 长按 `config.ini` 文件，点击“共享”，即可选择编辑App(例如 Koder)进行编辑
- 长按 `mys_goods_tool.log` 文件，点击”快速查看“即可查看日志
  
<div>
  <img src="https://user-images.githubusercontent.com/63289359/180296305-a7935e73-035d-4048-88ef-b9cee1c49893.PNG" alt="IMG_0848"/>
  <img src="https://user-images.githubusercontent.com/63289359/180296330-195587d5-7180-4f6d-81d0-52961ff36047.PNG" alt="IMG_0851"/>
  <img src="https://user-images.githubusercontent.com/63289359/180296846-dfe4c975-55f4-4ced-b6ad-c75a94a018c3.PNG" alt="IMG_0850"/>
<div/>
