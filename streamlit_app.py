"""
压缩文件处理器 - 网页版
支持 RAR、ZIP、7z 格式的文件提取
"""

import os
import shutil
import zipfile
import py7zr
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import streamlit as st
from pathlib import Path

# 页面配置
st.set_page_config(
    page_title="📦 压缩文件处理器",
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 支持的压缩格式
SUPPORTED_FORMATS = {
    '.rar': 'RAR文件',
    '.zip': 'ZIP文件',
    '.7z': '7z文件',
    '.tar': 'TAR文件',
    '.gz': 'GZIP文件',
    '.bz2': 'BZIP2文件',
    '.xz': 'XZ文件'
}

def should_skip_file(filename, skip_user_files, skip_patterns):
    """判断是否应该跳过文件"""
    if skip_user_files:
        patterns = [p.strip() for p in skip_patterns.split(',') if p.strip()]
        for pattern in patterns:
            if filename.startswith(pattern):
                return True, pattern
    return False, None

def process_single_file(file_path, output_dir, first_folder, all_content, skip_user_files, skip_patterns):
    """处理单个文件"""
    try:
        # 计算相对路径
        if first_folder:
            relative_path = file_path[len(first_folder) + 1:]
        else:
            relative_path = file_path
        
        # 检查是否应该跳过
        skip, pattern = should_skip_file(relative_path, skip_user_files, skip_patterns)
        if skip:
            return {'status': 'skipped', 'name': relative_path, 'reason': f'匹配规则: {pattern}'}
        
        dest_path = os.path.join(output_dir, relative_path)
        dest_dir = os.path.dirname(dest_path)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)
        
        # 写入文件内容
        if file_path in all_content:
            with open(dest_path, 'wb') as target:
                target.write(all_content[file_path].read())
        
        return {'status': 'copied', 'name': relative_path}
    except Exception as e:
        return {'status': 'error', 'name': relative_path, 'error': str(e)}

def process_archive(archive_file, output_dir, max_workers, progress_bar, status_text, skip_user_files, skip_patterns):
    """处理压缩文件"""
    try:
        # 读取文件数据
        file_data = archive_file.getvalue()
        
        # 检测真实文件类型
        if len(file_data) < 4:
            return {'error': '文件太小，无法识别格式'}
        
        # 通过魔数检测文件类型
        is_rar = file_data[:4] == b'Rar!' or file_data[:4] == b'\x52\x61\x72\x21'
        is_zip = file_data[:2] == b'PK'
        is_7z = file_data[:6] == b'\x37\x7A\xBC\xAF\x27\x1C'
        
        if is_zip:
            archive_obj = zipfile.ZipFile(archive_file)
            file_list = archive_obj.namelist()
        elif is_7z:
            with tempfile.NamedTemporaryFile(suffix='.7z', delete=False) as tmp_file:
                tmp_file.write(file_data)
                tmp_path = tmp_file.name
            archive_obj = py7zr.SevenZipFile(tmp_path, mode='r')
            file_list = archive_obj.getnames()
            temp_file_path = tmp_path
        elif is_rar:
            with tempfile.NamedTemporaryFile(suffix='.rar', delete=False) as tmp_file:
                tmp_file.write(file_data)
                tmp_path = tmp_file.name
            archive_obj = py7zr.SevenZipFile(tmp_path, mode='r')
            file_list = archive_obj.getnames()
            temp_file_path = tmp_path
        else:
            return {'error': '无法识别的压缩文件格式'}
        
        if not file_list:
            return {'error': '压缩文件为空'}
        
        # 获取第一层文件夹
        first_folder = None
        for name in file_list:
            if '/' in name:
                potential_folder = name.split('/')[0]
                if potential_folder and not name.endswith('/'):
                    first_folder = potential_folder
                    break
        
        if not first_folder:
            first_folder = ''
            files_to_process = [f for f in file_list if not f.endswith('/')]
        else:
            prefix = first_folder + '/'
            files_to_process = [
                f for f in file_list 
                if not f.endswith('/') and f.startswith(prefix)
            ]
        
        total_files = len(files_to_process)
        status_text.text(f"找到 {total_files} 个文件需要处理")
        
        copied_count = 0
        skipped_count = 0
        error_count = 0
        
        # 读取所有文件内容到内存
        all_content = archive_obj.read(files_to_process)
        
        # 使用线程池处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for file_path in files_to_process:
                future = executor.submit(
                    process_single_file,
                    file_path, output_dir, first_folder, all_content, skip_user_files, skip_patterns
                )
                futures.append(future)
            
            # 处理结果
            completed = 0
            for future in as_completed(futures):
                completed += 1
                progress = completed / total_files
                progress_bar.progress(progress)
                
                result = future.result()
                if result['status'] == 'copied':
                    copied_count += 1
                elif result['status'] == 'skipped':
                    skipped_count += 1
                else:
                    error_count += 1
        
        # 清理
        archive_obj.close()
        
        # 删除临时文件
        if 'temp_file_path' in locals():
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        
        return {
            'success': True,
            'copied': copied_count,
            'skipped': skipped_count,
            'errors': error_count,
            'output_dir': output_dir
        }
        
    except Exception as e:
        return {'error': str(e)}

def main():
    # 标题
    st.title("📦 压缩文件处理器")
    st.markdown("支持 RAR、ZIP、7z 格式的文件提取")
    
    # 侧边栏 - 设置
    with st.sidebar:
        st.header("⚙️ 设置")
        
        max_workers = st.slider("线程数", 1, 16, 4, help="同时处理的文件数量")
        
        st.subheader("文件过滤")
        skip_user_files = st.checkbox("跳过 'User.' 开头的文件", value=True)
        skip_patterns = st.text_input(
            "自定义跳过规则（逗号分隔）",
            value="User.,temp_,.",
            help="以这些前缀开头的文件将被跳过"
        )
        
        # 保存到 session state
        st.session_state['skip_user_files'] = skip_user_files
        st.session_state['skip_patterns'] = skip_patterns
        
        st.markdown("---")
        st.markdown("**支持的格式:**")
        for ext, desc in SUPPORTED_FORMATS.items():
            st.markdown(f"- {ext} {desc}")
    
    # 主界面 - 文件上传
    st.subheader("📤 上传压缩文件")
    uploaded_file = st.file_uploader(
        "拖拽或选择压缩文件",
        type=list(SUPPORTED_FORMATS.keys()),
        help="支持 RAR、ZIP、7z 格式"
    )
    
    if uploaded_file:
        st.success(f"已选择: {uploaded_file.name}")
        
        # 显示文件信息
        file_size = uploaded_file.size / 1024 / 1024  # MB
        st.info(f"文件大小: {file_size:.2f} MB")
        
        # 开始处理
        st.subheader("🚀 开始处理")
        
        if st.button("开始处理", type="primary", use_container_width=True):
            # 创建临时输出目录
            output_dir = tempfile.mkdtemp()
            
            # 进度条
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 在线程中处理（避免阻塞UI）
            def run_processing():
                return process_archive(
                    uploaded_file, output_dir, max_workers,
                    progress_bar, status_text,
                    st.session_state.get('skip_user_files', True),
                    st.session_state.get('skip_patterns', 'User.,temp_,.')
                )
            
            with st.spinner("正在处理..."):
                result = run_processing()
            
            if 'error' in result:
                st.error(f"处理失败: {result['error']}")
            else:
                # 显示结果
                st.success("✅ 处理完成！")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("复制文件", result['copied'])
                col2.metric("跳过文件", result['skipped'])
                col3.metric("错误文件", result['errors'])
                
                # 列出处理的文件
                with st.expander("📋 查看处理的文件列表"):
                    try:
                        for item in os.listdir(output_dir):
                            item_path = os.path.join(output_dir, item)
                            if os.path.isdir(item_path):
                                st.markdown(f"📁 {item}/")
                                sub_items = os.listdir(item_path)[:10]
                                for sub_item in sub_items:
                                    st.markdown(f"   - {sub_item}")
                                if len(os.listdir(item_path)) > 10:
                                    st.markdown(f"   ... 共 {len(os.listdir(item_path))} 个文件")
                            else:
                                size = os.path.getsize(item_path) / 1024
                                st.markdown(f"📄 {item} ({size:.1f} KB)")
                    except Exception:
                        st.markdown("文件列表无法显示")
                
                # 下载按钮
                st.subheader("📥 下载结果")
                
                if os.path.exists(output_dir) and os.listdir(output_dir):
                    zip_base = f"{Path(uploaded_file.name).stem}_extracted"
                    zip_path = os.path.join(tempfile.gettempdir(), f"{zip_base}.zip")
                    shutil.make_archive(
                        zip_path.replace('.zip', ''),
                        'zip',
                        output_dir
                    )
                    
                    with open(zip_path, 'rb') as f:
                        st.download_button(
                            label="📥 下载所有文件 (ZIP)",
                            data=f,
                            file_name=f"{zip_base}.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                else:
                    st.info("没有文件需要下载")

if __name__ == "__main__":
    main()