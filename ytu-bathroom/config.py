import toml


config = toml.load("config.toml")

# 数据库配置
DATABASE_URI = config['database']['uri']

# 趣智校园
QZXY_USER = config['qzxy']['user']
QZXY_PASSWORD = config['qzxy']['password']