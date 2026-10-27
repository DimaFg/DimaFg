import { site } from "@/config/site";

export function ContactInformation() {
  return (
    <div className="contact-info">
      <dl>
        <div className="row">
          <dt>Telegram</dt>
          <dd>
            <a href={site.telegram.url} target="_blank" rel="noopener noreferrer" data-analytics="telegram_click">
              @{site.telegram.handle} <span aria-hidden="true">→</span>
            </a>
          </dd>
        </div>
        <div className="row">
          <dt>Telegram-канал</dt>
          <dd>
            <a href={site.telegramChannel.url} target="_blank" rel="noopener noreferrer" data-analytics="telegram_click">
              @{site.telegramChannel.handle} <span aria-hidden="true">→</span>
            </a>
          </dd>
        </div>
        <div className="row">
          <dt>Почта</dt>
          <dd>
            <a href={`mailto:${site.email}`} data-analytics="email_click">
              {site.email}
            </a>
          </dd>
        </div>
        <div className="row">
          <dt>Город съёмки</dt>
          <dd>{site.region}</dd>
        </div>
        <div className="row">
          <dt>Ответ</dt>
          <dd>{site.responseTime}</dd>
        </div>
      </dl>
      <p className="contact-note">
        Если удобнее без формы — напишите в Telegram или на почту. Заявки с сайта сохраняются, даже
        если мессенджер временно недоступен: я увижу каждую.
      </p>
    </div>
  );
}
