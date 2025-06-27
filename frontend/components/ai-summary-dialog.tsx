import {
  AlertCircle,
  Bot,
  Clock,
  Loader2,
  MessageSquare,
  Sparkles,
  User,
} from 'lucide-react';
import { useState } from 'react';

import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { useAuth } from '@/contexts/AuthContext';
import { summarizeConversation } from '@/lib/api';
import { ChatUser, SummarizeResponse } from '@/lib/types';

interface AISummaryDialogProps {
  chatUser: ChatUser;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AISummaryDialog({
  chatUser,
  isOpen,
  onOpenChange,
}: AISummaryDialogProps) {
  const { token } = useAuth();
  const [messageCount, setMessageCount] = useState([10]);
  const [summary, setSummary] = useState<SummarizeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateSummary = async () => {
    if (!token) return;

    setIsLoading(true);
    setError(null);
    setSummary(null);

    try {
      const response = await summarizeConversation(
        {
          other_user_id: chatUser.id,
          message_count: messageCount[0],
        },
        token,
      );

      setSummary(response);

      if (!response.success) {
        setError(response.error || 'Failed to generate summary');
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'An unexpected error occurred';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const resetDialog = () => {
    setSummary(null);
    setError(null);
    setMessageCount([10]);
  };

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      resetDialog();
    }
    onOpenChange(open);
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-500" />
            AI Conversation Summary
          </DialogTitle>
          <DialogDescription>
            Generate an AI summary of your conversation with{' '}
            <span className="font-medium">
              {chatUser.full_name || chatUser.username}
            </span>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {!summary && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="message-count">
                  Number of recent messages to analyze
                </Label>
                <div className="px-3">
                  <Slider
                    id="message-count"
                    min={1}
                    max={50}
                    step={1}
                    value={messageCount}
                    onValueChange={setMessageCount}
                    className="w-full"
                  />
                  <div className="flex justify-between text-sm text-muted-foreground mt-1">
                    <span>1</span>
                    <span className="font-medium">
                      {messageCount[0]} messages
                    </span>
                    <span>50</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Bot className="h-4 w-4" />
                <span>Powered by Gemini AI</span>
              </div>

              <Button
                onClick={handleGenerateSummary}
                disabled={isLoading}
                className="w-full"
                size="lg"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating Summary...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    Generate Summary
                  </>
                )}
              </Button>
            </div>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {summary && summary.success && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <MessageSquare className="h-5 w-5" />
                      Conversation Summary
                    </span>
                    <div className="flex gap-2">
                      <Badge variant="secondary" className="text-xs">
                        <User className="h-3 w-3 mr-1" />
                        {summary.conversation_partner}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {summary.message_count} messages
                      </Badge>
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="prose prose-sm max-w-none">
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">
                      {summary.summary}
                    </p>
                  </div>
                </CardContent>
              </Card>

              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    Generated at {summary.generated_at}
                  </span>
                  <span className="flex items-center gap-1">
                    <Bot className="h-3 w-3" />
                    {summary.model_used}
                  </span>
                </div>
              </div>

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={resetDialog}
                  className="flex-1"
                >
                  Generate New Summary
                </Button>
                <Button
                  variant="default"
                  onClick={() => handleOpenChange(false)}
                  className="flex-1"
                >
                  Close
                </Button>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
