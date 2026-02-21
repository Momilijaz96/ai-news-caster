/**
 * Send AI News Caster briefing via WhatsApp.
 *
 * Usage:
 *   node send_whatsapp.js <mp3_path> <summary_json_path> <target_number>
 *
 * Environment:
 *   WHATSAPP_SESSION - base64-encoded session JSON (optional, falls back to local .wwebjs_auth)
 *
 * target_number format: "971XXXXXXXXX" (country code, no +, no spaces)
 */

const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const fs = require('fs');
const path = require('path');

const [,, mp3Path, summaryPath, targetNumber] = process.argv;

if (!mp3Path || !summaryPath || !targetNumber) {
  console.error('Usage: node send_whatsapp.js <mp3_path> <summary_json_path> <target_number>');
  process.exit(1);
}

// If WHATSAPP_SESSION env var is set, write it to disk for LocalAuth to pick up
const SESSION_DIR = path.join(__dirname, '.wwebjs_auth');
if (process.env.WHATSAPP_SESSION) {
  const sessionData = Buffer.from(process.env.WHATSAPP_SESSION, 'base64').toString('utf8');
  fs.mkdirSync(path.join(SESSION_DIR, 'session'), { recursive: true });
  fs.writeFileSync(path.join(SESSION_DIR, 'session', 'session.json'), sessionData);
  console.log('Session loaded from environment.');
}

const client = new Client({
  authStrategy: new LocalAuth({ dataPath: SESSION_DIR }),
  puppeteer: {
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  },
});

client.on('qr', (qr) => {
  // Only needed for first-time setup
  require('qrcode-terminal').generate(qr, { small: true });
  console.log('Scan the QR code above to authenticate WhatsApp.');
});

client.on('ready', async () => {
  console.log('WhatsApp client ready. Sending briefing...');

  const chatId = `${targetNumber}@c.us`;

  try {
    // 1. Send voice note (MP3)
    const mp3Data = fs.readFileSync(mp3Path);
    const mp3Base64 = mp3Data.toString('base64');
    const voiceMedia = new MessageMedia('audio/mpeg', mp3Base64, path.basename(mp3Path));
    await client.sendMessage(chatId, voiceMedia, { sendAudioAsVoice: true });
    console.log('Voice note sent.');

    // 2. Build and send text summary
    const stories = JSON.parse(fs.readFileSync(summaryPath, 'utf8'));
    const today = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
    let text = `*🎙️ AI News Briefing — ${today}*\n\n`;
    stories.forEach((story, i) => {
      text += `${i + 1}. *${story.title}*\n`;
      text += `   _${story.source}_ — ${story.link}\n\n`;
    });
    text += '_Daily briefing by AI News Caster_';

    await client.sendMessage(chatId, text);
    console.log('Text summary sent.');

  } catch (err) {
    console.error('Failed to send:', err);
    process.exit(1);
  }

  await client.destroy();
  process.exit(0);
});

client.on('auth_failure', (msg) => {
  console.error('Auth failure:', msg);
  process.exit(1);
});

client.initialize();
