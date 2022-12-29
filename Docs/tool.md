# `tool` 工具 使用说明
**❕注意：`tool`工具即[`tool.py`](/tool.py)，或`tool.exe`**

适用于 **v1.4.1** 即当前版本


## 功能 - 查询商品ID
可查询可兑换商品的 `Good_ID` ，把想兑换的商品的`Good_ID`填入 `config.ini` 中。

## 功能 - ❕登录并一键获取Cookie
根据程序中的提示进行操作（填写两次短信验证码）
> 1. 进入 https://user.mihoyo.com/#/login/captcha
> 2. 在浏览器中输入手机号并获取验证码，但**不要使用验证码登录**
> 3. 在程序中输入**手机号以及验证码** - 用于获取login_ticket (不会发送给任何第三方服务器，项目开源安全)
> 4. 刷新页面，再次进入 https://user.mihoyo.com/#/login/captcha
> 5. 在浏览器中输入刚才所用的手机号并获取验证码，但**不要使用验证码登录**
> 6. 在程序中输入**验证码** - 用于获取cookie_token等 (不会发送给任何第三方服务器，项目开源安全)
> 7. 完成


## 功能 - 从抓包导出文件分析获取Cookies
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
> - 请查看 [📃补全Cookie 部分](#功能---补全cookie)

2⃣️ 得到抓包导出的 文件/文件夹 以后，选择 `tool` 工具中的相关功能，根据你的导出文件类型( HttpCanary 导出的文件夹 / Stream 或其他工具导出的 `.har` 文件 )进行选择。

3⃣️ 输入抓包导出的 文件/文件夹 路径，即可查找Cookies，随后可以手动或让程序自动填入 `config.ini` 中。

**❕注意：从 v1.3.0 开始，写入的Cookies两边将不再包含引号 `'` `"` ，引号将是可有可无的，不影响 `config.ini` 文件的识别**

**❕注意：新版本米游社App抓包获取的Cookie中`stoken`为"v2"类型(开头为`v2__`末尾为`==`)，Cookie还需要有`mid`才行，本程序可以查找到`mid`。**

其他：`config.ini` 将不再包含单独的`stoken`项，但若需要兑换游戏内物品，则 `Cookie` 项中仍需要含有`stoken`


## 功能 - 补全Cookie
**短信登录获取的Cookie不需要进行补全！**  
由于网页版米游社Cookie不包含兑换游戏内物品所需的 `stoken`，因此需要获取 `stoken`，补全Cookie。  
另一种情况是没能从App抓包数据中找到 `stoken`，config.ini 配置文件中的Cookie需要补全。

以下是网页版米游社Cookie补全的步骤（程序中会有提示）：
1. 登录: https://user.mihoyo.com/ 和 https://bbs.mihoyo.com/dby/  
2. 在浏览器两个页面分别打开开发者模式，进入控制台，复制粘贴下面的语句(不包含换行)并回车
```javascript
var cookie=document.cookie;var ask=confirm('是否保存到剪切板?\nCookie查找结果：'+cookie);if(ask==true){copy(cookie);msg=cookie}else{msg='Cancel'}
```
3. 分别粘贴第一次和第二次查找到的Cookie
4. 完成


## 功能 - 查询送货地址ID
**需要提前配置好 `config.ini` 中的 `Cookie` 项**

可查询自己的的 `Address_ID` ，可以手动或让程序自动填入 `config.ini` 中。


## 功能 - 检查更新
可获取 [🔗GitHub latest realse](https://github.com/Ljzd-PRO/Mys_Goods_Tool/releases/latest) 最新发行版

需要注意，如果你使用的是 [🔗GitHub Actions](https://github.com/Ljzd-PRO/Mys_Goods_Tool/actions) 中下载的beta版本，检查更新功能将认为你的程序不是当前最新版本。
