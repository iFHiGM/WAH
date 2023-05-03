set -e

echo "Hi, this is WAH's and script."

export EMACS_SOURCE_PATH='C:\Users\FLMW\Documents\Code\github/emacs'
export EMACS_INSTALL_PATH='C:\Users\FLMW\Documents\Self/Emacs'
export IS_INCLUDE_TREE_SITTER=true
export IS_DRY_RUN=false

echo "=可配置项目："
echo "=Emacs源代码位置[$EMACS_SOURCE_PATH]"
echo "=Emacs安装位置[$EMACS_INSTALL_PATH]"
echo "=是否包含tree-sitter[$IS_INCLUDE_TREE_SITTER]"
echo "=是否演示运行[$IS_DRY_RUN]"

echo "=开始执行安装脚本..."

./how/installation.sh && \
   echo -e "=\e[32m安装脚本执行完成，请手动配置后续流程。\e[0m" || \
   echo -e "=\e[31m安装脚本执行失败，请检查安装过程日志。\e[0m"
