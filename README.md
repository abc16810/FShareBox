<div align="center">
<h1>文件分享柜-轻量</h1>
<h2>FShareBox - Lite</h2>
<p><em>6位匿名口令分享文本，文件，并像拿快递一样取文件 </em></p>
</div>

> 本项目参考【[FileCodeBox](https://github.com/vastsa/FileCodeBox)】开发

## 主要特色

- [x] 轻量简洁：Fastapi+Sqlite3+bootstrap+jquery
- [x] 轻松上传：复制粘贴，本地文件选择
- [x] 多种类型：文本，文件
- [x] 防止爆破：错误次数限制
- [x] 防止滥用：IP限制上传次数
- [x] 口令分享：(数字+字符)随机口令，存取文件，自定义次数以及有效期
- [x] 匿名分享：无需注册，无需登录
- [x] 管理面板：查看所有上传列表，后台删除等
- [x] 一键部署：docker一键部署
- [x] 多种存储方式：~~腾讯存储桶~~、本地文件流
- [x] 日志打印

## 部署
```
docker build -t FShareBox:v1 .
docker run --name FShareBox -v $PWD/data:/app/data FShareBox:v1
```
## 预览

### 取件
![index](./images/index.png)
![index2](./images/index_2.png)
![index3](./images/index3.png)
### 上传
![upload](./images/upload.png)
![upload2](./images/upload2.png)

### 后台管理
![admin](./images/admin.png)
![admin2](./images/admin2.png)