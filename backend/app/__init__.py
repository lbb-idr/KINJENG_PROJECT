"""
MiroFish Backend - Flask应用工厂
"""

import os
import time
import warnings

# 抑制 multiprocessing resource_tracker 的警告（来自第三方库如 transformers）
# 需要在所有其他导入之前设置
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import NotFound

from .config import Config
from .utils.logger import setup_logger, get_logger
from .auth import auth_bp, init_jwt


def create_app(config_class=Config):
    """Flask应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 设置JSON编码：确保中文直接显示（而不是 \uXXXX 格式）
    # Flask >= 2.3 使用 app.json.ensure_ascii，旧版本使用 JSON_AS_ASCII 配置
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False
    
    # 设置日志
    logger = setup_logger('mirofish')
    
    # 只在 reloader 子进程中打印启动信息（避免 debug 模式下打印两次）
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process
    
    if should_log_startup:
        logger.info("=" * 50)
        logger.info("MiroFish Backend 启动中...")
        logger.info("=" * 50)
    
    # 启用CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 初始化 DatabaseManager (SQLite)
    from .utils.database import DatabaseManager
    DatabaseManager().init_app(app)
    if should_log_startup:
        logger.info(f"数据库路径: {Config.SQLITE_PATH}")

    # Init JWT
    init_jwt(app)

    # 初始化 TaskManager 持久化存储
    from .models.task import TaskManager
    storage_dir = os.path.join(app.config.get('UPLOAD_FOLDER', os.path.join(app.root_path, '..', 'uploads')), 'tasks')
    TaskManager().init_storage(storage_dir)
    if should_log_startup:
        logger.info(f"任务存储目录: {storage_dir}")

    # Register cleanup on server shutdown (keep)
    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info("已注册模拟进程清理函数")

    # Init Metrics
    from .utils.monitoring import MetricsCollector
    metrics = MetricsCollector()
    metrics.init()

    # Init Sentry
    if Config.SENTRY_DSN:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        sentry_sdk.init(
            dsn=Config.SENTRY_DSN,
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.1,
        )
        if should_log_startup:
            logger.info("Sentry 已初始化")
    
    # Request log (keep touch for /health endpoint timestamp, no auto-shutdown)
    from .api.system import touch

    @app.before_request
    def before_request_with_metrics():
        touch()
        request.environ['_start_time'] = time.time()
        logger = get_logger('mirofish.request')
        logger.debug(f"请求: {request.method} {request.path}")
        if request.content_type and 'json' in request.content_type:
            logger.debug(f"请求体: {request.get_json(silent=True)}")
    
    @app.after_request
    def after_request_with_metrics(response):
        start = request.environ.get('_start_time')
        if start:
            latency = time.time() - start
            error = response.status_code >= 400
            metrics.record_request(request.path, latency, error)
        logger = get_logger('mirofish.request')
        logger.debug(f"响应: {response.status_code}")
        return response
    
    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    from .api import graph_bp, simulation_bp, report_bp, survey_bp, cognitive_bp, system_bp
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    app.register_blueprint(survey_bp, url_prefix='/api/survey')
    app.register_blueprint(cognitive_bp, url_prefix='/api/cognitive')
    app.register_blueprint(system_bp, url_prefix='/api/system')
    
    # 健康检查
    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'MiroFish Backend'}
    
    # Metrics endpoint
    @app.route('/api/metrics')
    def get_metrics():
        from .utils.monitoring import MetricsCollector
        return MetricsCollector().get_metrics()
    
    # Serve frontend SPA (catch-all for non-API paths)
    frontend_dir = os.path.join(app.root_path, '..', 'frontend')
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path.startswith('api/'):
            from flask import abort
            abort(404)
        try:
            return send_from_directory(frontend_dir, path or 'index.html')
        except NotFound:
            return send_from_directory(frontend_dir, 'index.html')
    
    if should_log_startup:
        logger.info("MiroFish Backend 启动完成")
    
    return app

