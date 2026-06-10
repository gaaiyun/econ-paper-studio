# 文档地图

这个目录放详细文档。根目录的 `README.md` 负责快速说明项目是什么、怎么跑；这里负责把实际使用中的细节讲清楚。

| 文档 | 适合谁看 | 内容 |
|---|---|---|
| `QUICKSTART_CN.md` | 第一次使用的人 | 从安装到跑完最小案例 |
| `DESIGN.md` | 想理解产品设计的人 | 设计思路、三层框架、工作平面、核心对象、状态机、证据链、上游参考如何被吸收 |
| `CLI_REFERENCE.md` | 要查命令的人 | 每个命令的参数、输出和常见用法 |
| `AGENT_RUNBOOK.md` | 让 agent 接手项目的人 | 接手顺序、必须加载的 skills、质量闸门 |
| `AGENT_INTEGRATIONS.md` | 要接入 OpenCode / Claude Code / Codex / Cursor / Coze 的人 | 各平台入口、推荐提示词、Coze runner 边界 |
| `SKILL_LOADOUT.md` | 配置 Claude/Codex/Cursor skills 的人 | 本项目依赖和推荐配套加载的技能清单 |
| `UPSTREAM_SKILLS.md` | 部署 agent skill bundle 的人 | 上游技能安装、加载顺序、安全边界和来源 |
| `../research_skill_registry.yaml` | agent runner / 技能编排 | 上游 skills 的任务路由和阶段映射 |
| `PROJECT_STRUCTURE.md` | 维护项目的人 | 目录、哪些文件该提交、哪些只是本地产物 |
| `QUALITY_GATES.md` | 要投稿或交付的人 | 数据、计量、写作、引用和复现检查 |

如果只想跑起来，先看 `QUICKSTART_CN.md`。如果想知道为什么这样设计，先看 `DESIGN.md`。如果是让 agent 长时间接手研究任务，先看 `AGENT_RUNBOOK.md`、`AGENT_INTEGRATIONS.md`、`SKILL_LOADOUT.md` 和 `UPSTREAM_SKILLS.md`。
