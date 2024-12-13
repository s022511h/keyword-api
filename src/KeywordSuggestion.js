import React, { useState, useEffect, useCallback } from 'react';

const API_BASE_URL = 'https://afternoon-thicket-53273-c58812e2a86f.herokuapp.com';

const KeywordSuggestion = () => {
  const [content, setContent] = useState('');
  const [optimizedContent, setOptimizedContent] = useState('');
  const [seoScore, setSeoScore] = useState(0);
  const [targetSeoScore, setTargetSeoScore] = useState(0);
  const [highlightedKeywords, setHighlightedKeywords] = useState([]);
  const [suggestedKeywords, setSuggestedKeywords] = useState([]);
  const [showGuide, setShowGuide] = useState(false);

  const cleanKeywords = (keywords) => keywords.map(keyword => keyword.replace(/\*\*/g, ''));

  const calculateSeoScore = useCallback((text) => {
    const wordCount = text.trim().split(/\s+/).length;
    const cleanedKeywords = cleanKeywords(highlightedKeywords);
    const keywordCount = cleanedKeywords.reduce((count, keyword) => {
      const keywordMatches = (text.match(new RegExp(`\\b${keyword}\\b`, 'gi')) || []).length;
      return count + keywordMatches;
    }, 0);
    const keywordDensity = (keywordCount / wordCount) * 100;
    const adjustedScore = Math.min(keywordDensity * 2, 100);

    setSeoScore(Math.round(adjustedScore));
  }, [highlightedKeywords]);

  useEffect(() => {
    calculateSeoScore(optimizedContent || content);
  }, [optimizedContent, content, highlightedKeywords, calculateSeoScore]);

  const fetchKeywords = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/optimize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: content }),
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();
      setOptimizedContent(data.optimizedText || '');
      setHighlightedKeywords(data.highlightedKeywords || []);
      setSeoScore(Math.round(data.currentSeoScore || 0));
      setTargetSeoScore(Math.round(data.targetSeoScore || 0));
      setSuggestedKeywords(data.highlightedKeywords);

    } catch (error) {
      console.error("Error fetching keywords:", error);
    }
  };

  const handleRewrite = () => fetchKeywords();

  const highlightKeywords = (text) => {
    let highlightedText = text;
    const cleanedKeywords = cleanKeywords(highlightedKeywords);

    cleanedKeywords.forEach((keyword) => {
      const escapedKeyword = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(`\\b${escapedKeyword}\\b`, 'gi');
      highlightedText = highlightedText.replace(regex, '<mark>$&</mark>');
    });

    return { __html: highlightedText };
  };

  const handleContentChange = (e) => {
    setOptimizedContent(e.target.innerText);
    calculateSeoScore(e.target.innerText);
  };

  const addKeywordToOptimizedContent = (keyword) => {
    const currentContent = optimizedContent;
    const keywordRegex = new RegExp(`\\b${keyword}\\b`, 'gi');

    if (!keywordRegex.test(currentContent)) {
      const sentences = currentContent.split(/(\.|\?|!)/);
      if (sentences.length > 1) {
        sentences[1] += ` ${keyword}`;
        const updatedContent = sentences.join('');
        setOptimizedContent(updatedContent);
      } else {
        setOptimizedContent((prevContent) => `${prevContent} ${keyword}`);
      }
    }
    calculateSeoScore(optimizedContent + " " + keyword);
  };

  const toggleGuide = () => setShowGuide(!showGuide);

  return (
    <div className="container">
      <h1>Keyword Optimiser</h1>
      <h2 className="title">Optimise Your Content</h2>
      <textarea
        value={content}
        onChange={e => setContent(e.target.value)}
        placeholder="Paste your content here"
        rows="10"
        cols="50"
        className="textarea"
      />
      <br />
      <button onClick={handleRewrite} className="button">Optimise Content</button>
      <h3 className="subtitle">Original Content:</h3>
      <textarea
        value={content}
        readOnly
        rows="10"
        cols="50"
        className="textarea"
      />
      <h3 className="subtitle">Optimised Content (Editable):</h3>
      <div
        className="optimizedContentBox"
        contentEditable
        dangerouslySetInnerHTML={highlightKeywords(optimizedContent)}
        onInput={handleContentChange}
      />
      <h3 className="subtitle">Target SEO Score: {targetSeoScore}%</h3>
      <h3 className="subtitle">Your Current SEO Score: {seoScore}%</h3>
      <h3 className="subtitle">Suggested Keywords:</h3>
      <div>
        {suggestedKeywords.map((keyword, index) => (
          <button key={index} className="keywordButton" onClick={() => addKeywordToOptimizedContent(keyword)}>
            {keyword}
          </button>
        ))}
      </div>
      <p className="seoText">The higher the SEO score, the better optimised your content is for search engines.</p>

      <button className="guideButton" onClick={toggleGuide}>Guide</button>
      {showGuide && (
        <div className="guideModal">
          <div className="guideContent">
            <h2>Content Optimisation Guide</h2>
            <ul>
              <li><strong>Paste Your Content</strong>: Start by pasting the content you want to optimise.</li>
              <li><strong>Click “Optimise Content”</strong>: This will analyse your text and suggest keywords to improve SEO.</li>
              <li><strong>Review and Edit</strong>: The “Optimised Content” box will show your content with keyword suggestions added. You can make any changes here.</li>
              <li><strong>Check Your Score</strong>: See how well your content scores compared to the target SEO score.</li>
              <li><strong>Use Suggested Keywords</strong>: Click on any suggested keyword to add it naturally to your content.</li>
            </ul>
            <button onClick={toggleGuide} className="closeButton">Close</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default KeywordSuggestion;
