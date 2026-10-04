import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User, X, Sparkles, Loader2 } from 'lucide-react';

const Chatbot = ({ onClose }) => {
  const [messages, setMessages] = useState([
    {
      sender: 'ai',
      text: "👋 Hi! I'm CoolRoute AI. I can answer ANY question about urban heat islands, tree planting, your city, or even general topics. What would you like to know?"
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Simulated AI response - Replace with actual API call
  const generateResponse = async (userMessage) => {
    setIsTyping(true);

    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Simple keyword-based responses for demo
    // In production, replace this with actual API call to your backend
    const lowerMsg = userMessage.toLowerCase();
    let response = '';

    if (lowerMsg.includes('heat island') || lowerMsg.includes('uhi')) {
      response = "Urban Heat Islands occur when cities replace natural land cover with dense concentrations of pavement, buildings, and other surfaces that absorb and retain heat. This effect can raise temperatures by 1-7°C compared to rural areas! Our project identifies these zones using satellite data and recommends targeted tree planting.";
    } else if (lowerMsg.includes('tree') || lowerMsg.includes('plant')) {
      response = "Trees cool the environment through transpiration (releasing water vapor) and providing shade. A single mature tree can cool the surrounding area by 2-8°C! We recommend Neem, Peepal, and Banyan for maximum cooling in Indian cities. The optimal density is 30-40 trees per hectare in urban areas.";
    } else if (lowerMsg.includes('budget') || lowerMsg.includes('cost') || lowerMsg.includes('money')) {
      response = `With your current budget of ₹${(500000).toLocaleString()}, you can plant approximately 1,000 Neem trees or 1,400 Gulmohar trees. The ROI calculator shows a net benefit of ₹2.3L over 5 years through energy savings. Would you like me to optimize the species mix for maximum cooling?`;
    } else if (lowerMsg.includes('equity') || lowerMsg.includes('poor') || lowerMsg.includes('income')) {
      response = "Our equity-weighted algorithm prioritizes low-income wards because they face disproportionate heat exposure but have the least resources for adaptation. Ward 23 and Ward 101 are flagged as high-priority due to income levels below 4/10 combined with temperatures above 45°C.";
    } else if (lowerMsg.includes('chennai') || lowerMsg.includes('city')) {
      response = "Chennai experiences severe UHI effects with surface temperatures reaching 47°C in summer. The highest risk zones are T. Nagar, Anna Nagar, and parts of Guindy due to high building density and low green cover. Our model recommends 1,247 trees across 18 hotspot zones.";
    } else if (lowerMsg.includes('how') || lowerMsg.includes('work')) {
      response = "CoolRoute works in 4 steps: (1) Satellite imagery (Landsat/Sentinel) captures surface temperatures, (2) XGBoost ML model predicts heat based on building density, roads, vegetation, and demographics, (3) Optimization engine ranks planting locations by equity × cooling ÷ cost, (4) Interactive 3D map shows exactly where to plant with GPS coordinates!";
    } else if (lowerMsg.includes('hello') || lowerMsg.includes('hi')) {
      response = "Hello! I'm ready to help with anything about urban cooling, climate science, or your specific project data. I can also discuss general topics! What interests you?";
    } else {
      response = "That's an interesting question! While my primary expertise is in urban heat island mitigation and tree planting optimization, I can tell you that sustainable urban planning involves multiple interconnected factors. For your specific project, I'd recommend focusing on the ward-level data in the 3D map. Would you like me to explain any specific ward's heat profile, or discuss the optimization algorithm in detail?";
    }

    setIsTyping(false);
    return response;
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = input.trim();
    setMessages(prev => [...prev, { sender: 'user', text: userMsg }]);
    setInput('');

    const aiResponse = await generateResponse(userMsg);

    // Type out the response character by character
    setMessages(prev => [...prev, { sender: 'ai', text: '' }]);

    let currentText = '';
    for (let i = 0; i < aiResponse.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 15));
      currentText += aiResponse[i];
      setMessages(prev => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1] = { sender: 'ai', text: currentText };
        return newMessages;
      });
    }
  };

  return (
    <div className="w-96 h-[550px] glass-panel flex flex-col shadow-2xl shadow-cyan-500/20">
      {/* Header */}
      <div className="p-4 bg-gradient-to-r from-cyan-500/20 via-purple-500/20 to-pink-500/20 rounded-t-2xl border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-r from-cyan-500 to-purple-600 flex items-center justify-center animate-pulse-glow">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="font-bold text-white text-sm">CoolRoute AI</h3>
            <p className="text-xs text-cyan-400 flex items-center gap-1">
              <span className="w-1.5 h-1.5 bg-heat-cool rounded-full animate-pulse" />
              Online • Ask anything
            </p>
          </div>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scroll">
        {messages.map((msg, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex gap-2 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
              msg.sender === 'user' 
                ? 'bg-cyan-500/20' 
                : 'bg-gradient-to-r from-cyan-500 to-purple-600'
            }`}>
              {msg.sender === 'user' ? (
                <User className="w-3.5 h-3.5 text-cyan-400" />
              ) : (
                <Bot className="w-3.5 h-3.5 text-white" />
              )}
            </div>
            <div className={`max-w-[80%] p-3 rounded-2xl text-sm leading-relaxed ${
              msg.sender === 'user'
                ? 'bg-cyan-500/20 text-cyan-100 rounded-tr-sm'
                : 'bg-white/5 text-gray-200 rounded-tl-sm'
            }`}>
              {msg.text}
              {msg.sender === 'ai' && msg.text === '' && isTyping && (
                <div className="flex gap-1 mt-1">
                  <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce" />
                  <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                  <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                </div>
              )}
            </div>
          </motion.div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Suggestions */}
      <div className="px-4 pb-2 flex gap-2 overflow-x-auto scrollbar-hide">
        {['What is UHI?', 'Best tree species?', 'How does it work?', 'Ward 23 analysis'].map((suggestion) => (
          <button
            key={suggestion}
            onClick={() => { setInput(suggestion); }}
            className="px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs text-gray-400 hover:text-cyan-400 hover:border-cyan-500/30 transition-all whitespace-nowrap"
          >
            {suggestion}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-white/10">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask anything about heat, trees, cities..."
            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/50 transition-colors"
          />
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleSend}
            disabled={isTyping || !input.trim()}
            className="p-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 text-white disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-cyan-500/20"
          >
            {isTyping ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </motion.button>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
