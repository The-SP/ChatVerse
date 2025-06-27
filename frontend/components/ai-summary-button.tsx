import { Sparkles } from 'lucide-react';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { ChatUser } from '@/lib/types';

import { AISummaryDialog } from './ai-summary-dialog';

interface AISummaryButtonProps {
  chatUser: ChatUser;
  className?: string;
  variant?: 'default' | 'outline' | 'ghost' | 'secondary';
  size?: 'default' | 'sm' | 'lg' | 'icon';
}

export function AISummaryButton({
  chatUser,
  className,
  variant = 'ghost',
  size = 'icon',
}: AISummaryButtonProps) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  return (
    <>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant={variant}
              size={size}
              onClick={() => setIsDialogOpen(true)}
              className={className}
            >
              <Sparkles className="h-4 w-4" />
              {size !== 'icon' && <span className="ml-2">AI Summary</span>}
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Generate AI summary of conversation</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <AISummaryDialog
        chatUser={chatUser}
        isOpen={isDialogOpen}
        onOpenChange={setIsDialogOpen}
      />
    </>
  );
}
