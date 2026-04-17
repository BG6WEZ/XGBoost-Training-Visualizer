"""
导出功能 Router

P1-T14: 配置/报告导出
提供配置导出（JSON/YAML）和报告导出（HTML/PDF）接口
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
import uuid
import json
import io

from app.database import get_db
from app.models import Experiment, Model, TrainingMetric, FeatureImportance, ExperimentStatus, ModelVersion
from app.schemas.export import ConfigExportResponse, ReportExportRequest, ReportExportMetadata

router = APIRouter()


def _build_config_export_data(experiment: Experiment) -> dict:
    config = experiment.config or {}
    return {
        "experiment_id": str(experiment.id),
        "experiment_name": experiment.name,
        "dataset_id": str(experiment.dataset_id) if experiment.dataset_id else None,
        "task_type": config.get("task_type"),
        "xgboost_params": config.get("xgboost_params", {}),
        "description": experiment.description,
        "tags": experiment.tags or [],
        "status": experiment.status,
        "created_at": experiment.created_at.isoformat() if experiment.created_at else None,
    }


@router.get("/experiments/{experiment_id}/export/config/json")
async def export_config_json(
    experiment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    导出实验配置为 JSON 格式
    
    返回完整的训练配置，包括：
    - XGBoost 参数
    - 数据集配置
    - 特征工程配置
    - 训练配置
    """
    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    result = await db.execute(
        select(Experiment).where(Experiment.id == exp_uuid)
    )
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    config_data = _build_config_export_data(experiment)

    json_content = json.dumps(config_data, indent=2, ensure_ascii=False)
    
    return StreamingResponse(
        iter([json_content.encode("utf-8")]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=config_{experiment_id}.json"}
    )


@router.get("/experiments/{experiment_id}/export/config/yaml")
async def export_config_yaml(
    experiment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    导出实验配置为 YAML 格式
    
    返回完整的训练配置，YAML 格式便于人工阅读和编辑
    
    注意：此功能需要 PyYAML 库
    如果依赖未安装，返回 503 错误
    """
    try:
        import yaml
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="YAML export requires PyYAML package. Please install it with: pip install pyyaml"
        )

    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    result = await db.execute(
        select(Experiment).where(Experiment.id == exp_uuid)
    )
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    config_data = _build_config_export_data(experiment)

    yaml_content = yaml.dump(config_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    return StreamingResponse(
        iter([yaml_content.encode("utf-8")]),
        media_type="text/yaml",
        headers={"Content-Disposition": f"attachment; filename=config_{experiment_id}.yaml"}
    )


@router.get("/experiments/{experiment_id}/export/report/html")
async def export_report_html(
    experiment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    导出实验报告为 HTML 格式
    
    包含完整的实验报告：
    - 实验基本信息
    - 训练配置
    - 最终指标
    - 指标历史曲线
    - 特征重要性
    - 模型版本信息
    """
    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    result = await db.execute(
        select(Experiment).where(Experiment.id == exp_uuid)
    )
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    model_result = await db.execute(
        select(Model).where(Model.experiment_id == exp_uuid)
    )
    model = model_result.scalar_one_or_none()

    metrics_result = await db.execute(
        select(TrainingMetric)
        .where(TrainingMetric.experiment_id == exp_uuid)
        .order_by(TrainingMetric.iteration)
    )
    metrics_history = metrics_result.scalars().all()

    fi_result = await db.execute(
        select(FeatureImportance)
        .where(FeatureImportance.experiment_id == exp_uuid)
        .order_by(FeatureImportance.rank)
    )
    feature_importance = fi_result.scalars().all()

    version_result = await db.execute(
        select(ModelVersion)
        .where(ModelVersion.experiment_id == exp_uuid)
        .where(ModelVersion.is_active == True)
        .order_by(ModelVersion.created_at.desc())
        .limit(1)
    )
    active_version = version_result.scalar_one_or_none()

    html_content = _generate_html_report(
        experiment=experiment,
        model=model,
        metrics_history=metrics_history,
        feature_importance=feature_importance,
        active_version=active_version
    )

    return StreamingResponse(
        iter([html_content.encode("utf-8")]),
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename=report_{experiment_id}.html"}
    )


@router.get("/experiments/{experiment_id}/export/report/pdf")
async def export_report_pdf(
    experiment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    导出实验报告为 PDF 格式
    
    注意：此功能需要额外的依赖（如 weasyprint 或 pdfkit）
    如果依赖未安装，返回 503 错误
    """
    try:
        from weasyprint import HTML
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="PDF export requires weasyprint package. Please install it with: pip install weasyprint"
        )

    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    result = await db.execute(
        select(Experiment).where(Experiment.id == exp_uuid)
    )
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    model_result = await db.execute(
        select(Model).where(Model.experiment_id == exp_uuid)
    )
    model = model_result.scalar_one_or_none()

    metrics_result = await db.execute(
        select(TrainingMetric)
        .where(TrainingMetric.experiment_id == exp_uuid)
        .order_by(TrainingMetric.iteration)
    )
    metrics_history = metrics_result.scalars().all()

    fi_result = await db.execute(
        select(FeatureImportance)
        .where(FeatureImportance.experiment_id == exp_uuid)
        .order_by(FeatureImportance.rank)
    )
    feature_importance = fi_result.scalars().all()

    version_result = await db.execute(
        select(ModelVersion)
        .where(ModelVersion.experiment_id == exp_uuid)
        .where(ModelVersion.is_active == True)
        .order_by(ModelVersion.created_at.desc())
        .limit(1)
    )
    active_version = version_result.scalar_one_or_none()

    html_content = _generate_html_report(
        experiment=experiment,
        model=model,
        metrics_history=metrics_history,
        feature_importance=feature_importance,
        active_version=active_version
    )

    pdf_bytes = HTML(string=html_content).write_pdf()

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{experiment_id}.pdf"}
    )


def _generate_html_report(
    experiment: Experiment,
    model: Optional[Model],
    metrics_history: list,
    feature_importance: list,
    active_version: Optional[ModelVersion] = None
) -> str:
    config = experiment.config or {}
    xgboost_params = config.get("xgboost_params", {})
    
    metrics_data = []
    for m in metrics_history:
        metrics_data.append({
            "iteration": m.iteration,
            "train_loss": m.train_loss,
            "val_loss": m.val_loss,
        })
    
    fi_data = []
    for fi in feature_importance:
        fi_data.append({
            "feature": fi.feature_name,
            "importance": fi.importance,
            "rank": fi.rank,
        })
    
    final_metrics = model.metrics if model else {}
    
    def format_loss(value):
        return f"{value:.4f}" if value is not None else "N/A"
    
    xgboost_params_rows = ''.join([f'<tr><td>{k}</td><td>{v}</td></tr>' for k, v in xgboost_params.items()])
    metrics_rows = ''.join([f'<tr><td>{k}</td><td class="metric-value">{v:.4f}</td></tr>' for k, v in final_metrics.items()]) if final_metrics else '<tr><td colspan="2">暂无指标数据</td></tr>'
    fi_rows = ''.join([f'<tr><td>{fi["rank"]}</td><td>{fi["feature"]}</td><td>{fi["importance"]:.4f}</td></tr>' for fi in fi_data[:20]])
    history_rows = ''.join([f'<tr><td>{m["iteration"]}</td><td>{format_loss(m["train_loss"])}</td><td>{format_loss(m["val_loss"])}</td></tr>' for m in metrics_data[-10:]])
    
    description_html = f'<p><strong>描述:</strong> {experiment.description}</p>' if experiment.description else ''
    
    completed_time_html = ''
    if experiment.updated_at and experiment.status == 'completed':
        completed_time_html = f'<p><strong>完成时间:</strong> {experiment.updated_at.strftime("%Y-%m-%d %H:%M:%S")}</p>'
    
    version_html = ''
    if active_version:
        version_html = f'''
    <div class="info-card">
        <h2>模型版本信息</h2>
        <p><strong>版本号:</strong> {active_version.version_number}</p>
        <p><strong>创建时间:</strong> {active_version.created_at.strftime("%Y-%m-%d %H:%M:%S") if active_version.created_at else "N/A"}</p>
        <p><strong>标签:</strong> {", ".join(active_version.tags) if active_version.tags else "无"}</p>
        {f'<p><strong>备注:</strong> {active_version.description}</p>' if active_version.description else ''}
    </div>
'''
    else:
        version_html = '''
    <div class="info-card">
        <h2>模型版本信息</h2>
        <p>暂无版本信息</p>
    </div>
'''
    
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>实验报告 - {experiment.name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{
            color: #1a1a1a;
            border-bottom: 2px solid #4a90d2;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #2c3e50;
            margin-top: 30px;
        }}
        .info-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #4a90d2;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }}
        th {{
            background: #f5f5f5;
        }}
        tr:nth-child(even) {{
            background: #fafafa;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <h1>实验报告</h1>
    
    <div class="info-card">
        <h2>实验信息</h2>
        <p><strong>实验名称:</strong> {experiment.name}</p>
        <p><strong>实验 ID:</strong> {experiment.id}</p>
        <p><strong>状态:</strong> {experiment.status}</p>
        <p><strong>创建时间:</strong> {experiment.created_at.strftime('%Y-%m-%d %H:%M:%S') if experiment.created_at else 'N/A'}</p>
        {completed_time_html}
        {description_html}
    </div>
    
    <h2>训练配置</h2>
    <table>
        <tr>
            <th>参数</th>
            <th>值</th>
        </tr>
        {xgboost_params_rows}
    </table>
    
    <h2>最终指标</h2>
    <div class="info-card">
        <table>
            <tr>
                <th>指标</th>
                <th>值</th>
            </tr>
            {metrics_rows}
        </table>
    </div>
    
    <h2>特征重要性</h2>
    <table>
        <tr>
            <th>排名</th>
            <th>特征</th>
            <th>重要性</th>
        </tr>
        {fi_rows}
    </table>
    
    <h2>训练历史</h2>
    <p>共 {len(metrics_data)} 次迭代</p>
    <table>
        <tr>
            <th>迭代</th>
            <th>训练损失</th>
            <th>验证损失</th>
        </tr>
        {history_rows}
    </table>
    
    {version_html}
    
    <div class="footer">
        <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>XGBoost Training Visualizer - 自动生成报告</p>
    </div>
</body>
</html>
"""
    return html
