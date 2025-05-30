# bjut.tech / score-notify

成绩查询 & 成绩发布提醒

## 介绍

本项目可以登录教务管理系统，获取用户本人的成绩信息；配合定时任务使用，可以在新成绩发布时通过邮件提醒。

### 统计数据计算

程序可以根据《北京工业大学本科生课程考核与成绩管理办法》（工大教发〔2024〕03 号）的相关规定，根据在教务管理系统中获取到的历史成绩信息，计算用户的成绩测评指标信息。这些信息包括：

- **加权平均分**：衡量学生在校期间学习质量的主要指标，计算方式为： $\sum\left({注册课程学分}\times{注册课程考核成绩}\right)/\sum{注册课程学分}$
- **正考加权平均分**：评优评奖、推荐免试的成绩依据，计算方式为： $\sum\left({注册课程学分}\times{注册课程正考考核成绩}\right)/\sum{注册课程学分}$
- **加权学分绩点（GPA）**：对外提供的成绩证明，计算方式为： $\sum\left({注册课程学分}\times{注册课程学分绩点}\right)/\sum{注册课程学分}$

根据规定，辅修专业课程、微专业课程、创新创业学分、自主课程和第二课堂的学分和成绩不计入上述计算。这些课程在提醒邮件中标记为“不计入”，在返回结果中通过 `included=False` 区分。

## 使用方法

### 配置项

- `CAS_USERNAME`：统一认证用户名（学号），必填
- `CAS_PASSWORD`：统一认证密码，非校园网环境下必填
- `JW_PASSWORD`：教务管理系统密码，若与 `CAS_PASSWORD` 相同则可以不填
- `JW_BASE_URL`：教务管理系统地址，默认为 `https://jwglxt.bjut.edu.cn`
- `NOTIFY_DRY_RUN`：通知时不发送邮件，直接在浏览器中显示邮件内容，默认为 `False`
- `NOTIFY_EMAIL`：接收通知的邮箱地址，除非已设置 `NOTIFY_DRY_RUN`，否则必填
- `ALIBABA_CLOUD_ACCESS_KEY_ID`：阿里云 AccessKey ID，用于发送邮件，除非已设置 `NOTIFY_DRY_RUN`，否则必填
- `ALIBABA_CLOUD_ACCESS_KEY_SECRET`：阿里云 AccessKey Secret，用于发送邮件，除非已设置 `NOTIFY_DRY_RUN`，否则必填

### 本地运行

安装依赖并在环境变量中设置配置项后，可以通过 `python -m score_notify` 运行程序

### 阿里云 FC

项目支持在阿里云函数计算环境，便于定时运行。在函数计算中可以通过层构建依赖，上传代码包后，将 handler 设置为 `handler.handler` 即可。传入的事件格式可见 `handler.py` 中注释说明。

## 已知问题

由于样本不足，对以下情况不保证可以正确处理

- 缓考成绩应计入正考加权
- 辅修、微专业成绩不应计入加权

欢迎提交 Pull Request 对这些问题或其他问题进行改正
