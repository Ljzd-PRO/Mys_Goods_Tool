# `tool` 工具 使用说明
**❕注意：`tool`工具即[`tool.py`](/tool.py)，或`tool.exe`**

## 功能 - 查询商品ID
可查询可兑换商品的 `Good_ID` ，把想兑换的商品的`Good_ID`填入 `config.ini` 中。

## 功能 - 查询送货地址ID
**需要提前配置好 `config.ini` 中的 `Cookie` 项**

可查询自己的的 `Address_ID` ，可以手动或让程序自动填入 `config.ini` 中。

## 功能 - ❕从抓包导出文件分析获取Cookies
1⃣️ 使用抓包软件进行抓包。

> ### Android 端
> - 建议使用 HttpCanary 进行抓包，需要注意Android 7之后可能需要Root或者设置平行世界等方法才能抓包
> - 筛选出域名为 **`api-takumi.mihoyo.com`** 的所有网络请求，全选它们并选择压缩导出，随后解压到本脚本程序所在的主机上。
> - 若某些Cookie项无法找到，额外筛选出域名为 **`bbs-api.mihoyo.com`** 的所有网络请求并导出

> ### iOS 端
> - 建议使用 [🔗Stream](https://apps.apple.com/cn/app/stream/id1312141691) App 进行抓包
> - 筛选出域名为 **`api-takumi.mihoyo.com`** 的所有网络请求，全选它们并轻点“导出HAR”，随后转移导出文件到本脚本程序所在的主机上。
> - 若某些Cookie项无法找到，额外筛选出域名为 **`bbs-api.mihoyo.com`** 的所有网络请求并导出

> ### 网页端
> - 关于网页版，目前米游社网页版的Cookies中似乎不包含`stoken`，因此如果需要兑换游戏内物品，无法使用浏览器获取Cookies


2⃣️ 得到抓包导出的 文件/文件夹 以后，选择 `tool` 工具中的相关功能，根据你的导出文件类型( HttpCanary 导出的文件夹 / Stream 或其他工具导出的 `.har` 文件 )进行选择。

3⃣️ 输入抓包导出的 文件/文件夹 路径，即可查找Cookies，随后可以手动或让程序自动填入 `config.ini` 中。

**❕注意：从 v1.3.0 开始，写入的Cookies两边将不再包含引号 `'` `"` ，引号将是可有可无的，不影响 `config.ini` 文件的识别**  
**另外，`config.ini` 将不再包含单独的`stoken`项，但若需要兑换游戏内物品，则 `Cookie` 项中仍需要含有`stoken`**

## 功能 - 检查更新
可获取 [🔗GitHub latest realse](https://github.com/Ljzd-PRO/Mys_Goods_Tool/releases/latest) 最新发行版

需要注意，如果你使用的是 [🔗GitHub Actions](https://github.com/Ljzd-PRO/Mys_Goods_Tool/actions) 中下载的beta版本，检查更新功能将认为你的程序不是当前最新版本。
