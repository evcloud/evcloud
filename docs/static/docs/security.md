
安全凭证是用于用户身份认证的凭证，iHarbor云对象存储服务提供了多种安全认证方式，如Session,Token,JWT。

## Auth Token认证 
Token密钥认证方式，使用简单，安全性相对较低，请及时定期刷新token。token的获取可以通过开放的API登录认证获取。每个用户同
一时刻只有一个有效的token，token永久有效，没有有效期，刷新创建新token，旧token会失效，如果token泄露，请及时创建新的
token，以防数据泄露丢失。    

Token应包含在Authorization HTTP标头中，密钥应以字符串文字“Token”为前缀，空格分隔两个字符串。
例如：   
`Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b`  

## JWT认证
Json web token认证方式，通过JWT API登录认证成功后会返回access jwt和refresh jwt 2个token，access jwt是调用API时的用户认证
凭证，有效期为2小时，access jwt失效后可以通过对应刷新API携带refresh jwt在有效期（2天）内刷新获取新的access jwt。
jwt应包含在Authorization HTTP标头中，密钥应以字符串文字“JWT”为前缀，空格分隔两个字符串，例如：   
`Authorization: JWT xxxx.xxxx.xxxx`















