#!/bin/bash
echo "========================================="
echo "  光储行业竞对量本利追踪系统 v2.2"
echo "  Energy Storage Competitor Intel"
echo "========================================="
echo ""
echo "  默认管理员: admin / admin123"
echo "  访问地址: http://localhost:8501"
echo ""
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
