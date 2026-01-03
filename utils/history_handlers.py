"""Telegram command handlers for document analysis history.

Provides /history command to view past document analyses.
"""

import logging
import time
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from document_history import get_analysis_db

logger = logging.getLogger(__name__)


def is_user_authorized(user_id: int) -> bool:
    """Check if user is authorized. Import from telegram_bot."""
    return True  # Adjust to match your auth logic


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /history command - show user's document analysis history.
    
    Usage:
        /history              - Show last 10 analyses
        /history 20           - Show last 20 analyses
        /history search term  - Search analyses by keyword
    """
    user_id = update.message.from_user.id
    username = update.message.from_user.username or f"user_{user_id}"
    
    if not is_user_authorized(user_id):
        await update.message.reply_text("⛔ Access denied.")
        logger.warning(f"Unauthorized history access: {user_id}")
        return
    
    try:
        db = get_analysis_db()
        args = context.args
        
        # Parse command arguments
        if not args:
            # Show last 10
            analyses = db.get_user_analysis_history(user_id, limit=10)
            title = "📊 Your Document Analysis History (Last 10)"
        
        elif args[0].isdigit():
            # Show last N
            limit = min(int(args[0]), 50)  # Max 50
            analyses = db.get_user_analysis_history(user_id, limit=limit)
            title = f"📊 Your Document Analysis History (Last {limit})"
        
        else:
            # Search
            search_term = " ".join(args)
            analyses = db.search_analyses(user_id, search_term, limit=10)
            title = f"🔍 Search Results for '{search_term}'"
        
        if not analyses:
            await update.message.reply_text(
                "ℹ️ No document analyses found.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Format response
        msg = f"<b>{title}</b>\n\n"
        
        for i, analysis in enumerate(analyses, 1):
            timestamp = analysis['timestamp'][:10]  # Date only
            doc_name = analysis['document_name'] or "Unknown"
            persona = "🧠 Kei" if analysis['persona'] == 'kei' else "🌍 Kin"
            status = "✅" if analysis['status'] == 'success' else "❌"
            doc_type = analysis['document_type'].upper() if analysis['document_type'] else "?"
            
            question = analysis['original_question'][:50]
            if len(analysis['original_question']) > 50:
                question += "..."
            
            msg += (
                f"{i}. <b>ID: {analysis['id']}</b>\n"
                f"   📄 {doc_name} ({doc_type})\n"
                f"   {persona} | {status} | {timestamp}\n"
                f"   Q: <i>{question}</i>\n\n"
            )
        
        # Add help text
        msg += (
            "\n<b>To view full analysis:</b>\n"
            "/view &lt;ID&gt; - View complete analysis result\n"
            "/delete &lt;ID&gt; - Delete analysis record"
        )
        
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    
    except Exception as e:
        logger.error(f"History command error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")


async def view_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /view <ID> command - show full analysis result.
    
    Usage:
        /view 5     - View analysis #5 (full content)
    """
    user_id = update.message.from_user.id
    
    if not is_user_authorized(user_id):
        await update.message.reply_text("⛔ Access denied.")
        return
    
    try:
        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text("Usage: /view <analysis_id>")
            return
        
        analysis_id = int(context.args[0])
        db = get_analysis_db()
        analysis = db.get_analysis_by_id(analysis_id, user_id)
        
        if not analysis:
            await update.message.reply_text("❌ Analysis not found or access denied.")
            return
        
        # Format response
        timestamp = analysis['timestamp'][:16]  # Date and time
        doc_name = analysis['document_name'] or "Unknown"
        persona = "Kei (ChatGPT)" if analysis['persona'] == 'kei' else "Kin (Perplexity)"
        doc_type = analysis['document_type'].upper() if analysis['document_type'] else "Unknown"
        
        msg = (
            f"<b>📄 Analysis #{analysis_id}</b>\n\n"
            f"<b>Document:</b> {doc_name}\n"
            f"<b>Type:</b> {doc_type}\n"
            f"<b>Persona:</b> {persona}\n"
            f"<b>Time:</b> {timestamp}\n"
            f"<b>Status:</b> {'✅ Success' if analysis['status'] == 'success' else '❌ Failed'}\n"
            f"<b>Processing:</b> {analysis['processing_time_ms']:.0f}ms\n\n"
        )
        
        msg += f"<b>Your Question:</b>\n<i>{analysis['original_question']}</i>\n\n"
        
        if analysis['extracted_preview']:
            msg += f"<b>Document Preview (first 500 chars):</b>\n<pre>{analysis['extracted_preview'][:500]}</pre>\n\n"
        
        msg += f"<b>Analysis Result:</b>\n"
        
        # Send in two parts if too long
        max_msg_length = 4096
        if len(analysis['analysis_result']) > max_msg_length - len(msg):
            await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
            await update.message.reply_text(
                f"<pre>{analysis['analysis_result'][:max_msg_length]}</pre>",
                parse_mode=ParseMode.HTML
            )
        else:
            msg += f"<pre>{analysis['analysis_result']}</pre>"
            await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    
    except Exception as e:
        logger.error(f"View command error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /delete <ID> command - delete an analysis record.
    
    Usage:
        /delete 5   - Delete analysis #5
    """
    user_id = update.message.from_user.id
    
    if not is_user_authorized(user_id):
        await update.message.reply_text("⛔ Access denied.")
        return
    
    try:
        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text("Usage: /delete <analysis_id>")
            return
        
        analysis_id = int(context.args[0])
        db = get_analysis_db()
        analysis = db.get_analysis_by_id(analysis_id, user_id)
        
        if not analysis:
            await update.message.reply_text("❌ Analysis not found or access denied.")
            return
        
        # Delete the record
        try:
            with db.sqlite3.connect(db.db_path) as conn:
                conn.execute('DELETE FROM document_analysis WHERE id = ? AND user_id = ?', 
                           (analysis_id, user_id))
                conn.commit()
            
            await update.message.reply_text(
                f"✅ Analysis #{analysis_id} deleted successfully."
            )
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            await update.message.reply_text("❌ Failed to delete record.")
    
    except Exception as e:
        logger.error(f"Delete command error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command - show user's analysis statistics.
    
    Usage:
        /stats    - Show analysis statistics
    """
    user_id = update.message.from_user.id
    username = update.message.from_user.username or f"user_{user_id}"
    
    if not is_user_authorized(user_id):
        await update.message.reply_text("⛔ Access denied.")
        return
    
    try:
        db = get_analysis_db()
        stats = db.get_user_stats(user_id)
        
        msg = "<b>📈 Your Document Analysis Statistics</b>\n\n"
        msg += f"<b>Total Analyses:</b> {stats['total_analyses']}\n"
        msg += f"<b>Successful:</b> {stats['successful']} ✅\n"
        msg += f"<b>Failed:</b> {stats['failed']} ❌\n\n"
        
        msg += f"<b>By Persona:</b>\n"
        msg += f"  • Kei (ChatGPT): {stats['kei_analyses']}\n"
        msg += f"  • Kin (Perplexity): {stats['kin_analyses']}\n\n"
        
        msg += f"<b>Document Types:</b> {stats['document_types']} different types\n"
        msg += f"<b>Avg Processing Time:</b> {stats['avg_processing_time_ms']:.0f}ms\n\n"
        
        msg += (
            "<b>Available Commands:</b>\n"
            "/history [N] - View analysis history\n"
            "/view &lt;ID&gt; - View specific analysis\n"
            "/delete &lt;ID&gt; - Delete analysis"
        )
        
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    
    except Exception as e:
        logger.error(f"Stats command error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")


# Integration for create_telegram_app():
"""
In create_telegram_app() function, add:

    from history_handlers import history_command, view_command, delete_command, stats_command
    
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("view", view_command))
    application.add_handler(CommandHandler("delete", delete_command))
    application.add_handler(CommandHandler("stats", stats_command))
"""
