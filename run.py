#!/usr/bin/env python3
"""
Run the Bitcoin Strategic Cycle Model Dashboard
"""

import uvicorn
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    print("""
    ═══════════════════════════════════════════════════════════════════════════
                    BTC ECONOMETRIC MODEL v7.6
                CoinGlass API + FRED | 12-Layer Engine
    ═══════════════════════════════════════════════════════════════════════════

    Starting server...
    Dashboard will be available at: http://localhost:8000

    Press Ctrl+C to stop the server.
    ═══════════════════════════════════════════════════════════════════════════
    """)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
