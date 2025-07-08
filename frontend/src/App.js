import React, { useState, useEffect } from 'react';
import dekDevLogo from './dekdev.png';

// Main App Component
const App = () => {
  const [jokes, setJokes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [voted, setVoted] = useState(false);
  const [votedIndex, setVotedIndex] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);

  const generateSessionId = () => {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
  };

  const fetchLeaderboard = async () => {
      try {
        const response = await fetch('/api/scores');
        const data = await response.json();
        setLeaderboard(data);
      } catch (error) {
        console.error('Error fetching leaderboard:', error);
      }
    };

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const handleGenerateJokes = async (context) => {
    setLoading(true);
    setVoted(false);
    setVotedIndex(null);
    const newSessionId = generateSessionId();
    setSessionId(newSessionId);

    try {
      const response = await fetch('/api/generate-jokes', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ context, session_id: newSessionId })
        });
        const data = await response.json();

        // ADD THESE DEBUG LINES:
        console.log("API Response:", data);
        console.log("Setting jokes to:", data);

        setJokes(data);
        console.log("API Response:", data);

      // Mock data for now
      // setTimeout(() => {
      //   setJokes([
      //     { id: 0, content: "Why don't firefighters ever get cold? Because they're always near something hot! Plus, their job really fires them up!", model: 'OpenAI' },
      //     { id: 1, content: "What did the firefighter say when asked about his favorite music? 'I prefer anything with a good beat... and no smoke on the water!'", model: 'Anthropic' },
      //     { id: 2, content: "How do firefighters stay in shape? They do ladder climbs and hose drills - it's the ultimate workout that's lit!", model: 'Gemini' },
      //     { id: 3, content: "Why did the firefighter become a comedian? Because he was already used to dealing with roasts!", model: 'Llama' }
      //   ]);
      //   setLoading(false);
      // }, 2000);
    } catch (error) {
      console.error('Error generating jokes:', error);
      setLoading(false);
    }
  };

  const handleVote = async (jokeIndex) => {
    if (voted) return;

    try {
      await fetch('/api/vote', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            model: jokes[jokeIndex].model,
            session_id: sessionId
          })
        });

      setVoted(true);
      setVotedIndex(jokeIndex);
      fetchLeaderboard();
    } catch (error) {
      console.error('Error submitting vote:', error);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#E6F3FF',
      fontFamily: 'Arial, sans-serif',
      padding: '20px'
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <Header />
        <JokeForm onGenerateJokes={handleGenerateJokes} loading={loading} />
        {jokes.length > 0 && (
          <JokeResults
            jokes={jokes}
            voted={voted}
            votedIndex={votedIndex}
            onVote={handleVote}
            loading={loading}
          />
        )}
        <Scoreboard leaderboard={leaderboard} />
          <Footer />
      </div>
    </div>
  );
};

// Header Component
const Header = () => (
  <div style={{ textAlign: 'center', marginBottom: '40px' }}>
    <h1 style={{
      color: '#1E3A8A',
      fontSize: '3rem',
      margin: '0 0 10px 0',
      fontWeight: 'bold'
    }}>
      🎭 Joke Battles
    </h1>
    <p style={{
      color: '#1E3A8A',
      fontSize: '1.2rem',
      margin: '0',
      opacity: 0.8
    }}>
      AI vs AI: Which model tells the best jokes?
    </p>
  </div>
);

// Joke Form Component
const JokeForm = ({ onGenerateJokes, loading }) => {
  const [context, setContext] = useState('');

  const handleSubmit = () => {
    if (context.trim() && !loading) {
      onGenerateJokes(context.trim());
    }
  };

  return (
    <div style={{
      backgroundColor: 'white',
      border: '2px solid #1E3A8A',
      borderRadius: '12px',
      padding: '30px',
      marginBottom: '40px',
      boxShadow: '0 4px 12px rgba(30, 58, 138, 0.1)'
    }}>
      <h2 style={{
        color: '#1E3A8A',
        marginBottom: '20px',
        fontSize: '1.5rem',
        textAlign: 'center'
      }}>
        What kind of joke would you like to hear?
      </h2>

      <div>
        <div style={{ marginBottom: '20px' }}>
          <input
            type="text"
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="e.g., a lighthearted joke about firefighters"
            style={{
              width: '100%',
              padding: '15px',
              fontSize: '1.1rem',
              border: '2px solid #93C5FD',
              borderRadius: '8px',
              outline: 'none',
              transition: 'border-color 0.3s'
            }}
            onFocus={(e) => e.target.style.borderColor = '#1E3A8A'}
            onBlur={(e) => e.target.style.borderColor = '#93C5FD'}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && context.trim() && !loading) {
                handleSubmit();
              }
            }}
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading || !context.trim()}
          style={{
            width: '100%',
            padding: '15px',
            fontSize: '1.1rem',
            backgroundColor: loading ? '#93C5FD' : '#1E3A8A',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'background-color 0.3s',
            fontWeight: 'bold'
          }}
        >
          {loading ? '🎲 Generating Jokes...' : '🎲 Generate Jokes'}
        </button>
      </div>

      <p style={{
        textAlign: 'center',
        marginTop: '15px',
        color: '#6B7280',
        fontSize: '0.9rem'
      }}>
        Four of the major AI models will compete to make you laugh. Vote for your favorite!
      </p>
    </div>
  );
};

// Joke Results Component
const JokeResults = ({ jokes, voted, votedIndex, onVote, loading }) => {
  const modelIcons = {
    'OpenAI': '🤖',
    'Anthropic': '🎭',
    'Gemini': '⭐',
    'Llama': '🦙'
  };

  return (
    <div style={{ marginBottom: '40px' }}>
      <h2 style={{
        color: '#1E3A8A',
        textAlign: 'center',
        marginBottom: '30px',
        fontSize: '1.5rem'
      }}>
        {voted ? 'Results Revealed!' : 'Choose Your Favorite Joke'}
      </h2>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '20px',
        marginBottom: '30px'
      }}>
        {jokes.map((joke, index) => (
          <div
            key={joke.id}
            style={{
              backgroundColor: 'white',
              border: `3px solid ${voted && index === votedIndex ? '#10B981' : '#1E3A8A'}`,
              borderRadius: '12px',
              padding: '25px',
              boxShadow: '0 4px 12px rgba(30, 58, 138, 0.1)',
              transition: 'transform 0.2s, border-color 0.3s',
              transform: voted && index === votedIndex ? 'scale(1.02)' : 'scale(1)',
              position: 'relative'
            }}
          >
            <div style={{
              textAlign: 'center',
              marginBottom: '15px',
              minHeight: '30px'
            }}>
              {voted ? (
                <div style={{
                  fontSize: '1.2rem',
                  fontWeight: 'bold',
                  color: '#1E3A8A',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px'
                }}>
                  <span style={{ fontSize: '1.5rem' }}>
                    {modelIcons[joke.model]}
                  </span>
                  {joke.model}
                  {index === votedIndex && (
                    <span style={{ color: '#10B981', fontSize: '1.5rem', marginLeft: '8px' }}>
                      ✓
                    </span>
                  )}
                </div>
              ) : (
                <div style={{
                  fontSize: '1.2rem',
                  fontWeight: 'bold',
                  color: '#6B7280'
                }}>
                  Anonymous Model {String.fromCharCode(65 + index)}
                </div>
              )}
            </div>

            <p style={{
              fontSize: '1rem',
              lineHeight: '1.6',
              color: '#374151',
              marginBottom: '20px',
              minHeight: '80px'
            }}>
              {joke.content}
            </p>

            {!voted && (
              <button
                onClick={() => onVote(index)}
                style={{
                  width: '100%',
                  padding: '12px',
                  backgroundColor: '#1E3A8A',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '1rem',
                  fontWeight: 'bold',
                  transition: 'background-color 0.3s'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#1E40AF'}
                onMouseOut={(e) => e.target.style.backgroundColor = '#1E3A8A'}
              >
                Vote for this joke
              </button>
            )}
          </div>
        ))}
      </div>

      {voted && (
        <div style={{ textAlign: 'center' }}>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: '15px 30px',
              backgroundColor: '#10B981',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '1.1rem',
              fontWeight: 'bold',
              transition: 'background-color 0.3s'
            }}
            onMouseOver={(e) => e.target.style.backgroundColor = '#059669'}
            onMouseOut={(e) => e.target.style.backgroundColor = '#10B981'}
          >
            🎲 Generate New Jokes
          </button>
        </div>
      )}
    </div>
  );
};

// Scoreboard Component
const Scoreboard = ({ leaderboard }) => {
  const maxVotes = Math.max(...leaderboard.map(item => item.votes));

  return (
    <div style={{
      backgroundColor: 'white',
      border: '2px solid #1E3A8A',
      borderRadius: '12px',
      padding: '30px',
      boxShadow: '0 4px 12px rgba(30, 58, 138, 0.1)'
    }}>
      <h2 style={{
        color: '#1E3A8A',
        textAlign: 'center',
        marginBottom: '30px',
        fontSize: '1.8rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '10px'
      }}>
        🏆 Leaderboard
      </h2>

      <div style={{ maxWidth: '600px', margin: '0 auto' }}>
        {leaderboard
          .sort((a, b) => b.votes - a.votes)
          .map((item, index) => (
            <div
              key={item.model}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '20px',
                marginBottom: '15px',
                backgroundColor: index === 0 ? '#FEF3C7' : '#F8FAFC',
                border: `2px solid ${index === 0 ? '#F59E0B' : '#E5E7EB'}`,
                borderRadius: '10px',
                transition: 'transform 0.2s'
              }}
              onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
              onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                <div style={{
                  fontSize: '2rem',
                  minWidth: '50px',
                  textAlign: 'center'
                }}>
                  {index === 0 ? '👑' : item.icon}
                </div>
                <div>
                  <div style={{
                    fontSize: '1.3rem',
                    fontWeight: 'bold',
                    color: '#1E3A8A'
                  }}>
                    {item.model}
                  </div>
                  <div style={{
                    fontSize: '0.9rem',
                    color: '#6B7280'
                  }}>
                    {((item.votes / leaderboard.reduce((sum, model) => sum + model.votes, 0)) * 100).toFixed(1)}% win rate
                  </div>
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div style={{
                  fontSize: '1.5rem',
                  fontWeight: 'bold',
                  color: '#1E3A8A'
                }}>
                  {item.votes}
                </div>
                <div style={{
                  fontSize: '0.9rem',
                  color: '#6B7280'
                }}>
                  votes
                </div>
              </div>
            </div>
          ))}
      </div>

      <p style={{
        textAlign: 'center',
        marginTop: '25px',
        color: '#6B7280',
        fontSize: '0.9rem'
      }}>
        Vote for your favorite jokes to influence the rankings!
      </p>
    </div>
  );
};

// Footer Component
const Footer = () => (
  <div style={{
    textAlign: 'center',
    padding: '30px 20px',
    marginTop: '40px',
    borderTop: '1px solid #93C5FD',
    backgroundColor: '#E6F3FF'
  }}>
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '12px',
      color: '#6B7280',
      fontSize: '1rem'
    }}>
      <span>Brought to you by</span>
      <img
        src={dekDevLogo}
        alt="Dek-Dev"
        style={{
          height: '32px',
          width: 'auto'
        }}
      />
    </div>
  </div>
);

export default App;